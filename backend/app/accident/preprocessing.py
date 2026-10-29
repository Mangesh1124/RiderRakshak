"""
Sensor Preprocessing Module.

Cleans and validates raw sensor readings before feature extraction.

Handles:
  - Missing/None values → replaced with safe defaults
  - Out-of-range values → clamped or flagged
  - Alcohol sensor noise → floor to 0
  - GPS sanity checks

Raw data is preserved; this module returns a new cleaned copy.
"""

import logging
from dataclasses import dataclass, replace
from typing import Optional, Tuple

from app.sensors.base import SensorReading, AccelerometerReading, GyroscopeReading, GPSReading

logger = logging.getLogger(__name__)

# ── Physical limits (sanity bounds) ──────────────────────────────────────────
# These represent physically plausible maximum values for motorcycle scenarios.
# Not validated against real hardware — adjust when hardware is available.
ACCEL_MAX = 150.0      # m/s² (very high impact)
ACCEL_MIN = -150.0
GYRO_MAX = 2000.0      # deg/s (MPU6050 max range)
GYRO_MIN = -2000.0
ALCOHOL_MAX = 1.0
ALCOHOL_MIN = 0.0
SPEED_MAX = 300.0      # km/h
SPEED_MIN = 0.0
LAT_MIN, LAT_MAX = -90.0, 90.0
LON_MIN, LON_MAX = -180.0, 180.0


@dataclass
class PreprocessedReading:
    """Cleaned sensor reading with metadata."""
    reading: SensorReading
    was_modified: bool
    modification_notes: list


def _clamp(value: float, min_val: float, max_val: float, name: str, notes: list) -> Tuple[float, list]:
    if value < min_val or value > max_val:
        clamped = max(min_val, min(max_val, value))
        notes.append(f"{name}: {value:.3f} → clamped to {clamped:.3f}")
        return clamped, notes
    return value, notes


def _safe_float(value, default: float, name: str, notes: list) -> Tuple[float, list]:
    if value is None or (isinstance(value, float) and (value != value)):  # NaN check
        notes.append(f"{name}: None/NaN → default {default}")
        return default, notes
    return float(value), notes


def preprocess_reading(reading: SensorReading) -> PreprocessedReading:
    """
    Clean and validate a raw sensor reading.

    Returns:
      PreprocessedReading with a cleaned SensorReading and modification metadata.
    """
    notes = []

    # ── Accelerometer ─────────────────────────────────────────────────────────
    ax, notes = _safe_float(reading.accelerometer.x, 0.0, "accel.x", notes)
    ay, notes = _safe_float(reading.accelerometer.y, 0.0, "accel.y", notes)
    az, notes = _safe_float(reading.accelerometer.z, 9.81, "accel.z", notes)

    ax, notes = _clamp(ax, ACCEL_MIN, ACCEL_MAX, "accel.x", notes)
    ay, notes = _clamp(ay, ACCEL_MIN, ACCEL_MAX, "accel.y", notes)
    az, notes = _clamp(az, ACCEL_MIN, ACCEL_MAX, "accel.z", notes)

    # ── Gyroscope ─────────────────────────────────────────────────────────────
    gx, notes = _safe_float(reading.gyroscope.x, 0.0, "gyro.x", notes)
    gy, notes = _safe_float(reading.gyroscope.y, 0.0, "gyro.y", notes)
    gz, notes = _safe_float(reading.gyroscope.z, 0.0, "gyro.z", notes)

    gx, notes = _clamp(gx, GYRO_MIN, GYRO_MAX, "gyro.x", notes)
    gy, notes = _clamp(gy, GYRO_MIN, GYRO_MAX, "gyro.y", notes)
    gz, notes = _clamp(gz, GYRO_MIN, GYRO_MAX, "gyro.z", notes)

    # ── Alcohol ───────────────────────────────────────────────────────────────
    alcohol, notes = _safe_float(reading.alcohol, 0.0, "alcohol", notes)
    alcohol = max(0.0, alcohol)  # floor to 0, no negative BAC
    if alcohol != reading.alcohol:
        notes.append(f"alcohol: floored to 0.0")

    # ── Speed ─────────────────────────────────────────────────────────────────
    speed, notes = _safe_float(reading.speed, 0.0, "speed", notes)
    speed, notes = _clamp(speed, SPEED_MIN, SPEED_MAX, "speed", notes)

    # ── GPS ───────────────────────────────────────────────────────────────────
    lat, notes = _safe_float(reading.gps.latitude, 18.5204, "gps.lat", notes)
    lon, notes = _safe_float(reading.gps.longitude, 73.8567, "gps.lon", notes)
    lat, notes = _clamp(lat, LAT_MIN, LAT_MAX, "gps.lat", notes)
    lon, notes = _clamp(lon, LON_MIN, LON_MAX, "gps.lon", notes)

    was_modified = len(notes) > 0
    if was_modified:
        logger.debug("Sensor preprocessing modified reading: %s", notes)

    # Build cleaned reading
    cleaned = SensorReading(
        timestamp=reading.timestamp,
        accelerometer=AccelerometerReading(x=ax, y=ay, z=az),
        gyroscope=GyroscopeReading(x=gx, y=gy, z=gz),
        gps=GPSReading(
            latitude=lat,
            longitude=lon,
            timestamp=reading.gps.timestamp,
            speed=speed,
        ),
        alcohol=round(alcohol, 4),
        speed=round(speed, 2),
        scenario=reading.scenario,
    )

    return PreprocessedReading(
        reading=cleaned,
        was_modified=was_modified,
        modification_notes=notes,
    )
