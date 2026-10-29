"""
Test: Preprocessing + Feature Extraction + Detection + Fusion + Severity
"""

import pytest
import math
from app.sensors.simulator import SimulatedSensorProvider
from app.sensors.base import SensorReading, AccelerometerReading, GyroscopeReading, GPSReading
from app.accident.preprocessing import preprocess_reading
from app.accident.features import extract_features, Features
from app.accident.threshold_detector import detect_accident
from app.accident.sensor_fusion import apply_sensor_fusion
from app.accident.severity import calculate_severity
from datetime import datetime


@pytest.fixture
def simulator():
    return SimulatedSensorProvider(seed=42)


def get_clean(simulator, scenario):
    raw = simulator.get_reading(scenario)
    return preprocess_reading(raw).reading


# ── Preprocessing Tests ───────────────────────────────────────────────────────

def test_preprocessing_returns_clean_reading(simulator):
    raw = simulator.get_reading("NORMAL")
    result = preprocess_reading(raw)
    assert result.reading is not None
    assert result.reading.alcohol >= 0.0


def test_preprocessing_clamps_negative_alcohol():
    """Alcohol cannot be negative after preprocessing."""
    from app.sensors.base import GPSReading
    fake = SensorReading(
        timestamp=datetime.utcnow(),
        accelerometer=AccelerometerReading(x=0.0, y=0.0, z=9.8),
        gyroscope=GyroscopeReading(x=0.0, y=0.0, z=0.0),
        gps=GPSReading(latitude=18.5, longitude=73.8),
        alcohol=-0.5,  # Invalid!
        speed=0.0,
        scenario="NORMAL",
    )
    result = preprocess_reading(fake)
    assert result.reading.alcohol == 0.0
    assert result.was_modified


def test_preprocessing_clamps_extreme_accel():
    """Extreme acceleration values get clamped."""
    fake = SensorReading(
        timestamp=datetime.utcnow(),
        accelerometer=AccelerometerReading(x=9999.0, y=0.0, z=9.8),
        gyroscope=GyroscopeReading(x=0.0, y=0.0, z=0.0),
        gps=GPSReading(latitude=18.5, longitude=73.8),
        alcohol=0.0, speed=0.0, scenario="NORMAL",
    )
    result = preprocess_reading(fake)
    assert result.reading.accelerometer.x <= 150.0
    assert result.was_modified


# ── Feature Extraction Tests ──────────────────────────────────────────────────

def test_feature_extraction_normal(simulator):
    clean = get_clean(simulator, "NORMAL")
    features = extract_features(clean)
    assert isinstance(features, Features)
    # Normal should have low magnitude
    assert features.acceleration_magnitude > 0
    assert features.tilt_angle >= 0


def test_acceleration_magnitude_formula():
    """Verify acceleration magnitude formula: sqrt(x² + y² + z²)."""
    fake = SensorReading(
        timestamp=datetime.utcnow(),
        accelerometer=AccelerometerReading(x=3.0, y=4.0, z=0.0),
        gyroscope=GyroscopeReading(x=0.0, y=0.0, z=0.0),
        gps=GPSReading(latitude=18.5, longitude=73.8),
        alcohol=0.0, speed=0.0, scenario="NORMAL",
    )
    features = extract_features(fake)
    expected = math.sqrt(3**2 + 4**2 + 0**2)  # 5.0
    assert abs(features.acceleration_magnitude - expected) < 0.001


def test_feature_extraction_accident_high_magnitude(simulator):
    """Accident features should have high acceleration magnitude."""
    magnitudes = []
    for _ in range(5):
        raw = simulator.get_reading("ACCIDENT")
        clean = preprocess_reading(raw).reading
        features = extract_features(clean)
        magnitudes.append(features.acceleration_magnitude)
    avg = sum(magnitudes) / len(magnitudes)
    assert avg > 20.0, f"Accident avg magnitude {avg:.2f} should be > 20 m/s²"


# ── Detection Tests ───────────────────────────────────────────────────────────

def test_normal_scenario_does_not_trigger_accident(simulator):
    """Normal riding must NOT produce CONFIRMED_ACCIDENT under prototype thresholds."""
    non_accident_count = 0
    for _ in range(10):
        clean = get_clean(simulator, "NORMAL")
        features = extract_features(clean)
        detection = detect_accident(features)
        fusion = apply_sensor_fusion(detection, features)
        if not fusion.is_accident:
            non_accident_count += 1
    # Normal should never trigger accident
    assert non_accident_count == 10, (
        f"Normal scenario triggered accident {10 - non_accident_count}/10 times"
    )


def test_accident_scenario_triggers_detection(simulator):
    """Accident scenario MUST produce is_accident=True in majority of runs."""
    accident_count = 0
    for _ in range(10):
        clean = get_clean(simulator, "ACCIDENT")
        features = extract_features(clean)
        detection = detect_accident(features)
        fusion = apply_sensor_fusion(detection, features)
        if fusion.is_accident:
            accident_count += 1
    assert accident_count >= 8, (
        f"Accident scenario triggered accident only {accident_count}/10 times"
    )


def test_detection_score_range():
    """Accident score must always be in [0.0, 1.0]."""
    sim = SimulatedSensorProvider()
    for scenario in ["NORMAL", "ACCIDENT", "FALL", "HIGH_TILT"]:
        for _ in range(3):
            clean = preprocess_reading(sim.get_reading(scenario)).reading
            features = extract_features(clean)
            result = detect_accident(features)
            assert 0.0 <= result.accident_score <= 1.0, (
                f"Score {result.accident_score} out of range for {scenario}"
            )


def test_detection_score_breakdown_complete():
    """Score breakdown must contain all expected keys."""
    sim = SimulatedSensorProvider()
    clean = preprocess_reading(sim.get_reading("ACCIDENT")).reading
    features = extract_features(clean)
    result = detect_accident(features)
    required_keys = {"impact", "tilt", "rotation", "deceleration", "speed_context"}
    assert required_keys.issubset(set(result.score_breakdown.keys()))


# ── Sensor Fusion Tests ───────────────────────────────────────────────────────

def test_fusion_does_not_produce_negative_score(simulator):
    """Fusion score must remain >= 0."""
    for scenario in ["NORMAL", "HARD_BRAKING", "FALL", "ACCIDENT"]:
        clean = get_clean(simulator, scenario)
        features = extract_features(clean)
        detection = detect_accident(features)
        fusion = apply_sensor_fusion(detection, features)
        assert fusion.final_score >= 0.0


def test_fusion_notes_populated():
    """Fusion must always populate notes."""
    sim = SimulatedSensorProvider()
    clean = preprocess_reading(sim.get_reading("ACCIDENT")).reading
    features = extract_features(clean)
    detection = detect_accident(features)
    fusion = apply_sensor_fusion(detection, features)
    assert len(fusion.fusion_notes) > 0


# ── Severity Tests ────────────────────────────────────────────────────────────

def test_severity_returns_valid_level(simulator):
    """Severity must return one of LOW/MEDIUM/HIGH/CRITICAL."""
    valid_levels = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
    clean = get_clean(simulator, "ACCIDENT")
    features = extract_features(clean)
    detection = detect_accident(features)
    fusion = apply_sensor_fusion(detection, features)
    severity_result = calculate_severity(fusion, features)
    assert severity_result.severity in valid_levels


def test_accident_scenario_high_severity():
    """Accident scenario should generally produce HIGH or CRITICAL severity."""
    # Use a new simulator with fixed seed for reproducibility
    from app.sensors.simulator import SimulatedSensorProvider
    sim = SimulatedSensorProvider(seed=0)
    high_count = 0
    for _ in range(10):
        clean = preprocess_reading(sim.get_reading("ACCIDENT")).reading
        features = extract_features(clean)
        detection = detect_accident(features)
        fusion = apply_sensor_fusion(detection, features)
        sev = calculate_severity(fusion, features)
        if sev.severity in {"HIGH", "CRITICAL"}:
            high_count += 1
    assert high_count >= 5, (
        f"Accident scenario produced HIGH/CRITICAL severity only {high_count}/10 times. "
        f"Note: Gaussian variability in simulation means not every reading is extreme."
    )
