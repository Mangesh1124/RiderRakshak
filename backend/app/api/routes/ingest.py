import math
import time
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.database.database import get_db
from app.database.models import SensorReading as SensorReadingModel
from app.sensors.base import (
    SensorReading, AccelerometerReading, GyroscopeReading, GPSReading,
)
from app.accident.preprocessing import preprocess_reading
from app.accident.features import extract_features
from app.accident.threshold_detector import detect_accident
from app.accident.sensor_fusion import apply_sensor_fusion
from app.accident.severity import calculate_severity
from app.emergency.alert_manager import create_pending_accident
from app.api.routes.simulation import _ensure_rider
from app.services.email_alert import (
    should_send_alcohol_email, alert_email_ready, send_alert_email,
)
from app.services.history import build_history

router = APIRouter(prefix="/api/sensors", tags=["Hardware Ingest"])

COOLDOWN_SECONDS = 30
_last_accident_time: dict = {}


class IngestPayload(BaseModel):
    rider_id: Optional[str] = None
    ax: float
    ay: float
    az: float
    gx: float
    gy: float
    gz: float
    alcohol: Optional[float] = 0.0
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    speed: Optional[float] = 0.0
    gps_fix: Optional[bool] = False


@router.post("/ingest")
def ingest(
    payload: IngestPayload,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    rider_id = payload.rider_id or settings.DEFAULT_RIDER_ID
    _ensure_rider(db, rider_id)

    use_gps = bool(
        payload.gps_fix
        and payload.latitude is not None
        and payload.longitude is not None
        and -90 <= payload.latitude <= 90
        and -180 <= payload.longitude <= 180
        and not (payload.latitude == 0 and payload.longitude == 0)
    )
    lat = payload.latitude if use_gps else settings.DEFAULT_LATITUDE
    lng = payload.longitude if use_gps else settings.DEFAULT_LONGITUDE
    speed_val = payload.speed if (use_gps and payload.speed is not None) else 0.0

    alc_in = payload.alcohol
    if alc_in is None or not math.isfinite(alc_in):
        alc_in = 0.0
    alcohol_val = max(0.0, alc_in)

    raw = SensorReading(
        timestamp=datetime.utcnow(),
        accelerometer=AccelerometerReading(payload.ax, payload.ay, payload.az),
        gyroscope=GyroscopeReading(payload.gx, payload.gy, payload.gz),
        gps=GPSReading(latitude=lat, longitude=lng),
        alcohol=alcohol_val,
        speed=speed_val,
        scenario="HARDWARE",
    )
    clean = preprocess_reading(raw).reading

    ax, ay, az = clean.accelerometer.x, clean.accelerometer.y, clean.accelerometer.z
    gx, gy, gz = clean.gyroscope.x, clean.gyroscope.y, clean.gyroscope.z
    acc_mag = math.sqrt(ax**2 + ay**2 + az**2)
    gyro_mag = math.sqrt(gx**2 + gy**2 + gz**2)
    tilt = math.degrees(math.atan2(math.sqrt(ax**2 + ay**2), abs(az)))

    db.add(SensorReadingModel(
        rider_id=rider_id, timestamp=clean.timestamp, scenario=clean.scenario,
        accel_x=ax, accel_y=ay, accel_z=az,
        gyro_x=gx, gyro_y=gy, gyro_z=gz,
        acceleration_magnitude=round(acc_mag, 4),
        gyro_magnitude=round(gyro_mag, 4),
        tilt_angle=round(tilt, 4),
        alcohol=clean.alcohol,
        latitude=clean.gps.latitude if use_gps else None,
        longitude=clean.gps.longitude if use_gps else None,
        speed=clean.speed,
    ))
    db.commit()

    features = extract_features(clean)
    detection = detect_accident(features)
    fusion = apply_sensor_fusion(detection, features)

    alcohol_trigger = should_send_alcohol_email(rider_id, clean.alcohol)

    accident_id = None
    accident_new = False
    severity = None
    if fusion.is_accident:
        now = time.time()
        if now - _last_accident_time.get(rider_id, 0) >= COOLDOWN_SECONDS:
            sev = calculate_severity(fusion, features)
            severity = sev.severity if sev else "UNKNOWN"
            accident = create_pending_accident(
                db=db,
                rider_id=rider_id,
                accident_score=fusion.final_score,
                classification=fusion.final_classification,
                severity=severity,
                latitude=clean.gps.latitude,
                longitude=clean.gps.longitude,
                sensor_snapshot=raw.to_dict(),
                features_snapshot=features.to_dict(),
                score_breakdown={
                    **{k: float(v) for k, v in detection.score_breakdown.items()},
                    "fusion_notes": fusion.fusion_notes,
                },
            )
            accident_id = accident.id
            _last_accident_time[rider_id] = now
            accident_new = True

    # ── Encrypted alert email with the previous N seconds of readings ─────────
    accident_email = accident_new and alert_email_ready()
    email_queued = False
    if alcohol_trigger or accident_email:
        history = build_history(
            db, rider_id, clean.scenario, clean.timestamp, settings.EMAIL_HISTORY_SECONDS
        )
        snapshot = {
            "alcohol": clean.alcohol,
            "gps_used": use_gps,
            "lat": clean.gps.latitude,
            "lng": clean.gps.longitude,
            "speed": clean.speed,
            "ax": ax, "ay": ay, "az": az,
            "gx": gx, "gy": gy, "gz": gz,
            "acc_mag": acc_mag,
            "tilt": tilt,
            "classification": fusion.final_classification,
            "score": fusion.final_score,
            "history": history,
        }
        if alcohol_trigger:
            background_tasks.add_task(send_alert_email, "ALCOHOL_DETECTED", rider_id, dict(snapshot))
        if accident_email:
            background_tasks.add_task(
                send_alert_email, "ACCIDENT_DETECTED", rider_id,
                {**snapshot, "accident_id": accident_id, "severity": severity},
            )
        email_queued = True

    return {
        "classification": fusion.final_classification,
        "score": fusion.final_score,
        "is_accident": fusion.is_accident,
        "accident_id": accident_id,
        "gps_used": use_gps,
        "alcohol": clean.alcohol,
        "alcohol_detected": clean.alcohol >= settings.ALCOHOL_ALERT_INDEX,
        "email_queued": email_queued,
    }