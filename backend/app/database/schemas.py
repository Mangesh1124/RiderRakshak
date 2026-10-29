"""
Pydantic Schemas (request/response models) for RideRakshak API.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


# ── Sensor Schemas ────────────────────────────────────────────────────────────

class AccelerometerData(BaseModel):
    x: float
    y: float
    z: float


class GyroscopeData(BaseModel):
    x: float
    y: float
    z: float


class GPSData(BaseModel):
    latitude: float
    longitude: float


class SensorReadingRaw(BaseModel):
    """Raw sensor reading from simulator or hardware gateway."""
    timestamp: datetime
    accelerometer: AccelerometerData
    gyroscope: GyroscopeData
    alcohol: float = 0.0
    gps: GPSData
    speed: float = 0.0
    scenario: str = "NORMAL"


class SensorReadingResponse(BaseModel):
    """Processed sensor reading returned by API."""
    id: int
    rider_id: str
    timestamp: datetime
    scenario: str

    accel_x: float
    accel_y: float
    accel_z: float
    gyro_x: float
    gyro_y: float
    gyro_z: float

    acceleration_magnitude: Optional[float]
    gyro_magnitude: Optional[float]
    tilt_angle: Optional[float]

    alcohol: float
    latitude: Optional[float]
    longitude: Optional[float]
    speed: float

    class Config:
        from_attributes = True


# ── Feature Schemas ───────────────────────────────────────────────────────────

class ExtractedFeatures(BaseModel):
    """Features extracted from a sensor reading window."""
    acceleration_magnitude: float
    gyro_magnitude: float
    tilt_angle: float
    peak_acceleration: float
    peak_gyro: float
    angular_velocity: float
    deceleration: float
    speed: float
    alcohol: float
    # Context
    scenario: str = "UNKNOWN"


# ── Accident Schemas ──────────────────────────────────────────────────────────

class DetectionResult(BaseModel):
    """Result from the accident detection pipeline."""
    classification: str          # NORMAL / SUSPICIOUS / POSSIBLE_ACCIDENT / CONFIRMED_ACCIDENT
    accident_score: float        # 0.0–1.0
    score_breakdown: Dict[str, float]
    is_accident: bool
    features: ExtractedFeatures


class AccidentResponse(BaseModel):
    """Accident event returned by API."""
    id: str
    rider_id: str
    timestamp: datetime
    accident_score: float
    classification: str
    severity: Optional[str]
    status: str
    cancellation_deadline: Optional[datetime]
    confirmed_at: Optional[datetime]
    cancelled_at: Optional[datetime]
    latitude: Optional[float]
    longitude: Optional[float]
    sensor_snapshot: Optional[Dict[str, Any]]
    features_snapshot: Optional[Dict[str, Any]]
    score_breakdown: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True


class AccidentListResponse(BaseModel):
    total: int
    accidents: List[AccidentResponse]


# ── Alert Schemas ─────────────────────────────────────────────────────────────

class EmergencyAlertResponse(BaseModel):
    id: int
    accident_id: str
    timestamp: datetime
    alert_type: str
    status: str
    recipient: Optional[str]
    message: str

    class Config:
        from_attributes = True


# ── Rider Schemas ─────────────────────────────────────────────────────────────

class RiderResponse(BaseModel):
    id: str
    name: str
    phone: Optional[str]
    emergency_contact: Optional[str]
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


# ── System Schemas ────────────────────────────────────────────────────────────

class SystemStatus(BaseModel):
    app_name: str
    version: str
    environment: str
    simulation_mode: bool
    database_status: str
    active_rider: str
    uptime_seconds: float
    timestamp: datetime


class SimulationRequest(BaseModel):
    scenario: str
    rider_id: Optional[str] = None
    auto_confirm: bool = False  # If True, skip cancellation window


class SimulationResponse(BaseModel):
    scenario: str
    sensor_reading: SensorReadingRaw
    features: ExtractedFeatures
    detection_result: DetectionResult
    accident_id: Optional[str] = None
    accident_status: Optional[str] = None
    alert_message: Optional[str] = None
    message: str
