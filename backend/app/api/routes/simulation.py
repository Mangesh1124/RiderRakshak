"""
Simulation API Routes.

POST /api/simulation/{scenario}
  Runs the full pipeline for a given scenario:
    sensor reading → preprocessing → feature extraction →
    threshold detection → sensor fusion → severity →
    accident creation (if detected) → alert simulation
"""

import logging
import math
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database.models import SensorReading as SensorReadingModel, Rider, EmergencyAlert
from app.database.schemas import (
    SimulationResponse, SensorReadingRaw,
    AccelerometerData, GyroscopeData, GPSData,
    ExtractedFeatures, DetectionResult as DetectionResultSchema
)
from app.sensors.simulator import SimulatedSensorProvider, VALID_SCENARIOS
from app.accident.preprocessing import preprocess_reading
from app.accident.features import extract_features
from app.accident.threshold_detector import detect_accident
from app.accident.sensor_fusion import apply_sensor_fusion
from app.accident.severity import calculate_severity
from app.emergency.alert_manager import create_pending_accident, confirm_accident
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/simulation", tags=["Simulation"])
_simulator = SimulatedSensorProvider()


def _ensure_rider(db: Session, rider_id: str) -> Rider:
    """Ensure rider exists in DB, create if not."""
    rider = db.query(Rider).filter(Rider.id == rider_id).first()
    if not rider:
        rider = Rider(id=rider_id, name=f"Rider {rider_id}")
        db.add(rider)
        db.commit()
        db.refresh(rider)
    return rider


@router.get("/scenarios")
def list_scenarios():
    """List all available simulation scenarios."""
    return {
        "scenarios": VALID_SCENARIOS,
        "mode": "SOFTWARE_SIMULATION",
    }


@router.post("/{scenario}", response_model=SimulationResponse)
def run_simulation(
    scenario: str,
    rider_id: str = None,
    auto_confirm: bool = False,
    db: Session = Depends(get_db),
):
    """
    Run the complete sensor-to-alert pipeline for a scenario.

    Steps:
      1. Generate sensor reading
      2. Preprocess
      3. Extract features
      4. Detect accident (threshold)
      5. Apply sensor fusion
      6. Calculate severity (if accident)
      7. Create pending accident (if accident detected)
      8. Return full result
    """
    scenario_upper = scenario.upper().replace("-", "_")
    if scenario_upper not in VALID_SCENARIOS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid scenario '{scenario}'. Valid: {VALID_SCENARIOS}"
        )

    rider_id = rider_id or settings.DEFAULT_RIDER_ID
    _ensure_rider(db, rider_id)

    # ── 1. Generate sensor reading ────────────────────────────────────────────
    raw_reading = _simulator.get_reading(scenario_upper)
    logger.info("Simulation | scenario=%s rider=%s", scenario_upper, rider_id)

    # ── 2. Preprocess ─────────────────────────────────────────────────────────
    preprocessed = preprocess_reading(raw_reading)
    clean = preprocessed.reading

    ax, ay, az = clean.accelerometer.x, clean.accelerometer.y, clean.accelerometer.z
    gx, gy, gz = clean.gyroscope.x, clean.gyroscope.y, clean.gyroscope.z
    acc_mag = math.sqrt(ax**2 + ay**2 + az**2)
    gyro_mag = math.sqrt(gx**2 + gy**2 + gz**2)
    tilt = math.degrees(math.atan2(math.sqrt(ax**2 + ay**2), abs(az)))

    # ── 3. Persist sensor reading to DB ───────────────────────────────────────
    db_reading = SensorReadingModel(
        rider_id=rider_id,
        timestamp=clean.timestamp,
        scenario=clean.scenario,
        accel_x=ax, accel_y=ay, accel_z=az,
        gyro_x=gx, gyro_y=gy, gyro_z=gz,
        acceleration_magnitude=round(acc_mag, 4),
        gyro_magnitude=round(gyro_mag, 4),
        tilt_angle=round(tilt, 4),
        alcohol=clean.alcohol,
        latitude=clean.gps.latitude,
        longitude=clean.gps.longitude,
        speed=clean.speed,
    )
    db.add(db_reading)
    db.commit()

    # ── 4. Feature extraction ─────────────────────────────────────────────────
    features = extract_features(clean)

    # ── 5. Accident detection ─────────────────────────────────────────────────
    detection = detect_accident(features)

    # ── 6. Sensor fusion ──────────────────────────────────────────────────────
    fusion = apply_sensor_fusion(detection, features)

    # ── 7. Severity (if accident) ─────────────────────────────────────────────
    severity_result = None
    if fusion.is_accident:
        severity_result = calculate_severity(fusion, features)

    # ── 8. Create pending accident if detected ────────────────────────────────
    accident_id = None
    accident_status = None
    alert_message = None

    if fusion.is_accident:
        severity_str = severity_result.severity if severity_result else "UNKNOWN"

        accident = create_pending_accident(
            db=db,
            rider_id=rider_id,
            accident_score=fusion.final_score,
            classification=fusion.final_classification,
            severity=severity_str,
            latitude=clean.gps.latitude,
            longitude=clean.gps.longitude,
            sensor_snapshot=raw_reading.to_dict(),
            features_snapshot=features.to_dict(),
            score_breakdown={**{k: float(v) for k, v in detection.score_breakdown.items()},
                             "fusion_notes": fusion.fusion_notes},
        )
        accident_id = accident.id
        accident_status = "PENDING"

        if auto_confirm:
            confirmed = confirm_accident(db, accident.id)
            accident_status = confirmed.status if confirmed else "CONFIRMED_ACCIDENT"
            db_alert = db.query(EmergencyAlert).filter(
                EmergencyAlert.accident_id == accident.id
            ).first()
            alert_message = db_alert.message if db_alert else None

        if not alert_message:
            alert_message = (
                f"Accident detected! ID: {accident_id} | "
                f"Status: {accident_status} | "
                f"Severity: {severity_str} | "
                f"Score: {fusion.final_score:.3f} | "
                f"Cancellation window: {settings.CANCELLATION_WINDOW_SECONDS}s"
            )
    else:
        alert_message = (
            f"No accident detected. "
            f"Score: {fusion.final_score:.3f} | "
            f"Classification: {fusion.final_classification}"
        )

    # ── Build response ────────────────────────────────────────────────────────
    sensor_resp = SensorReadingRaw(
        timestamp=clean.timestamp,
        accelerometer=AccelerometerData(x=ax, y=ay, z=az),
        gyroscope=GyroscopeData(x=gx, y=gy, z=gz),
        alcohol=clean.alcohol,
        gps=GPSData(latitude=clean.gps.latitude, longitude=clean.gps.longitude),
        speed=clean.speed,
        scenario=clean.scenario,
    )

    features_resp = ExtractedFeatures(
        acceleration_magnitude=features.acceleration_magnitude,
        gyro_magnitude=features.gyro_magnitude,
        tilt_angle=features.tilt_angle,
        peak_acceleration=features.peak_acceleration,
        peak_gyro=features.peak_gyro,
        angular_velocity=features.angular_velocity,
        deceleration=features.deceleration,
        speed=features.speed,
        alcohol=features.alcohol,
        scenario=features.scenario,
    )

    detection_resp = DetectionResultSchema(
        classification=fusion.final_classification,
        accident_score=fusion.final_score,
        score_breakdown=detection.score_breakdown,
        is_accident=fusion.is_accident,
        features=features_resp,
    )

    return SimulationResponse(
        scenario=scenario_upper,
        sensor_reading=sensor_resp,
        features=features_resp,
        detection_result=detection_resp,
        accident_id=accident_id,
        accident_status=accident_status,
        alert_message=alert_message,
        message=f"[SIMULATION MODE] Scenario: {scenario_upper} | {alert_message}",
    )
