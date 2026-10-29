"""
SQLAlchemy ORM Models for RideRakshak.

Tables:
  - riders
  - sensor_readings
  - accidents
  - emergency_alerts
"""

from datetime import datetime
from sqlalchemy import (
    Column, String, Float, Integer, Boolean,
    DateTime, ForeignKey, Text, JSON
)
from sqlalchemy.orm import relationship
from app.database.database import Base


class Rider(Base):
    """Represents a helmet/rider registration."""

    __tablename__ = "riders"

    id = Column(String, primary_key=True, index=True)          # e.g. RR001
    name = Column(String, nullable=False, default="Test Rider")
    phone = Column(String, nullable=True)
    emergency_contact = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Relationships
    sensor_readings = relationship("SensorReading", back_populates="rider")
    accidents = relationship("Accident", back_populates="rider")


class SensorReading(Base):
    """Raw + processed sensor reading snapshot."""

    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    rider_id = Column(String, ForeignKey("riders.id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    scenario = Column(String, default="NORMAL")

    # Accelerometer (m/s²)
    accel_x = Column(Float, nullable=False)
    accel_y = Column(Float, nullable=False)
    accel_z = Column(Float, nullable=False)

    # Gyroscope (deg/s)
    gyro_x = Column(Float, nullable=False)
    gyro_y = Column(Float, nullable=False)
    gyro_z = Column(Float, nullable=False)

    # Derived features
    acceleration_magnitude = Column(Float, nullable=True)
    gyro_magnitude = Column(Float, nullable=True)
    tilt_angle = Column(Float, nullable=True)

    # Other sensors
    alcohol = Column(Float, default=0.0)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    speed = Column(Float, default=0.0)

    # Relationships
    rider = relationship("Rider", back_populates="sensor_readings")


class Accident(Base):
    """Accident event record with full lifecycle tracking."""

    __tablename__ = "accidents"

    id = Column(String, primary_key=True, index=True)    # e.g. RR-ACC-20260925-0001
    rider_id = Column(String, ForeignKey("riders.id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Detection
    accident_score = Column(Float, nullable=False)
    classification = Column(String, nullable=False)  # NORMAL/SUSPICIOUS/POSSIBLE/CONFIRMED
    severity = Column(String, nullable=True)         # LOW/MEDIUM/HIGH/CRITICAL

    # Status
    status = Column(String, default="PENDING")       # PENDING/CONFIRMED/FALSE_ALERT_CANCELLED
    cancellation_deadline = Column(DateTime, nullable=True)
    confirmed_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)

    # Location at time of accident
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    # Sensor snapshot (JSON for flexibility)
    sensor_snapshot = Column(JSON, nullable=True)

    # Feature snapshot
    features_snapshot = Column(JSON, nullable=True)

    # Score breakdown for explainability
    score_breakdown = Column(JSON, nullable=True)

    # Relationships
    rider = relationship("Rider", back_populates="accidents")
    emergency_alerts = relationship("EmergencyAlert", back_populates="accident")


class EmergencyAlert(Base):
    """Emergency alert log (simulated GSM / future real SMS)."""

    __tablename__ = "emergency_alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    accident_id = Column(String, ForeignKey("accidents.id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    alert_type = Column(String, default="SIMULATED_GSM")  # SIMULATED_GSM / REAL_GSM (future)
    status = Column(String, default="SIMULATED_SENT")     # SIMULATED_SENT / FAILED / etc.
    recipient = Column(String, nullable=True)
    message = Column(Text, nullable=False)

    # Relationship
    accident = relationship("Accident", back_populates="emergency_alerts")
