"""
Feature Extraction Module.

Computes accident-relevant features from a preprocessed sensor reading.

Features are used by BOTH:
  1. Threshold-based detector (current)
  2. ML models (future / training pipeline)

This ensures consistent feature schema across the entire pipeline.
"""

import math
import logging
from dataclasses import dataclass

from app.sensors.base import SensorReading

logger = logging.getLogger(__name__)


@dataclass
class Features:
    """
    Extracted feature vector used for accident detection and ML training.

    All features are computed deterministically from a single SensorReading.
    """

    # Magnitude features
    acceleration_magnitude: float   # sqrt(ax² + ay² + az²)  m/s²
    gyro_magnitude: float           # sqrt(gx² + gy² + gz²)  deg/s

    # Orientation
    tilt_angle: float               # degrees from vertical

    # Peak values (useful for window-based detection)
    peak_acceleration: float        # same as magnitude for single reading
    peak_gyro: float                # same as gyro_magnitude for single reading

    # Dynamic features
    angular_velocity: float         # gyro magnitude alias (clarity)
    deceleration: float             # |accel.x| when negative (braking force)

    # Context
    speed: float                    # km/h
    alcohol: float                  # 0.0–1.0

    # Source scenario (for dataset labeling)
    scenario: str = "UNKNOWN"

    def to_dict(self) -> dict:
        return {
            "acceleration_magnitude": self.acceleration_magnitude,
            "gyro_magnitude": self.gyro_magnitude,
            "tilt_angle": self.tilt_angle,
            "peak_acceleration": self.peak_acceleration,
            "peak_gyro": self.peak_gyro,
            "angular_velocity": self.angular_velocity,
            "deceleration": self.deceleration,
            "speed": self.speed,
            "alcohol": self.alcohol,
            "scenario": self.scenario,
        }


def extract_features(reading: SensorReading) -> Features:
    """
    Extract feature vector from a preprocessed sensor reading.

    Args:
        reading: A PreprocessedReading.reading (cleaned SensorReading)

    Returns:
        Features dataclass with all computed values.
    """
    ax, ay, az = reading.accelerometer.x, reading.accelerometer.y, reading.accelerometer.z
    gx, gy, gz = reading.gyroscope.x, reading.gyroscope.y, reading.gyroscope.z

    # ── Acceleration Magnitude ─────────────────────────────────────────────────
    acc_mag = math.sqrt(ax**2 + ay**2 + az**2)

    # ── Gyroscope Magnitude ────────────────────────────────────────────────────
    gyro_mag = math.sqrt(gx**2 + gy**2 + gz**2)

    # ── Tilt Angle ─────────────────────────────────────────────────────────────
    # Angle between Z axis and gravity vector.
    # 0° = upright, 90° = horizontal, >90° = inverted
    # Uses only X and Y lateral components vs Z vertical
    tilt_radians = math.atan2(math.sqrt(ax**2 + ay**2), abs(az))
    tilt_angle = math.degrees(tilt_radians)

    # ── Deceleration ───────────────────────────────────────────────────────────
    # Captures braking intensity: negative ax = forward deceleration
    deceleration = abs(min(0.0, ax))

    # ── Peak Values ────────────────────────────────────────────────────────────
    # For single-reading analysis, peak == current magnitude.
    # For window-based ML: compute over sliding window.
    peak_acceleration = acc_mag
    peak_gyro = gyro_mag

    features = Features(
        acceleration_magnitude=round(acc_mag, 4),
        gyro_magnitude=round(gyro_mag, 4),
        tilt_angle=round(tilt_angle, 4),
        peak_acceleration=round(peak_acceleration, 4),
        peak_gyro=round(peak_gyro, 4),
        angular_velocity=round(gyro_mag, 4),
        deceleration=round(deceleration, 4),
        speed=round(reading.speed, 2),
        alcohol=round(reading.alcohol, 4),
        scenario=reading.scenario,
    )

    logger.debug(
        "Features extracted | acc_mag=%.2f gyro_mag=%.2f tilt=%.1f° dec=%.2f",
        features.acceleration_magnitude,
        features.gyro_magnitude,
        features.tilt_angle,
        features.deceleration,
    )

    return features
