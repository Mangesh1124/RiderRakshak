"""
Abstract base classes for sensor providers.
Enables hardware-agnostic architecture:

  SensorProvider
      ├── SimulatedSensorProvider   ← current
      └── HardwareSensorProvider    ← future (ESP32 + MPU6050)

The accident detection system works with SensorReading objects
regardless of their origin.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class AccelerometerReading:
    """Accelerometer data in m/s²."""
    x: float
    y: float
    z: float


@dataclass
class GyroscopeReading:
    """Gyroscope data in degrees/second."""
    x: float
    y: float
    z: float


@dataclass
class GPSReading:
    """GPS position data."""
    latitude: float
    longitude: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    speed: float = 0.0  # km/h


@dataclass
class SensorReading:
    """
    Complete sensor reading from any provider.
    This is the common interface between hardware and software.
    """
    timestamp: datetime
    accelerometer: AccelerometerReading
    gyroscope: GyroscopeReading
    gps: GPSReading
    alcohol: float = 0.0          # 0.0–1.0 normalized (0.08 = legal BAC limit)
    speed: float = 0.0            # km/h
    scenario: str = "NORMAL"

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "accelerometer": {
                "x": self.accelerometer.x,
                "y": self.accelerometer.y,
                "z": self.accelerometer.z,
            },
            "gyroscope": {
                "x": self.gyroscope.x,
                "y": self.gyroscope.y,
                "z": self.gyroscope.z,
            },
            "gps": {
                "latitude": self.gps.latitude,
                "longitude": self.gps.longitude,
            },
            "alcohol": self.alcohol,
            "speed": self.speed,
            "scenario": self.scenario,
        }


class SensorProvider(ABC):
    """
    Abstract sensor provider.
    Implement this interface to connect any hardware source.
    """

    @abstractmethod
    def get_reading(self, scenario: Optional[str] = None) -> SensorReading:
        """Return a sensor reading for the given scenario."""
        ...

    @abstractmethod
    def get_name(self) -> str:
        """Return provider name (e.g. 'SimulatedSensorProvider')."""
        ...


class GPSProvider(ABC):
    """
    Abstract GPS provider.
    Implement to connect real GPS hardware.
    """

    @abstractmethod
    def get_location(self) -> GPSReading:
        """Return current GPS location."""
        ...

    @abstractmethod
    def get_name(self) -> str:
        ...
