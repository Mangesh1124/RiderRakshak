"""
Sensor Simulator — Core module.

Generates deterministic and realistic sensor readings for each scenario.

Scenarios:
  NORMAL               → Normal riding
  HARD_BRAKING         → Sudden deceleration
  SUDDEN_ACCELERATION  → Quick throttle
  HIGH_TILT            → Sharp corner or near-fall
  FALL                 → Low-speed fall
  ACCIDENT             → High-impact collision
  ALCOHOL_DETECTED     → Rider has alcohol above threshold

IMPORTANT: This is a SOFTWARE SIMULATION.
All values are synthetic. They do not represent validated real-world hardware readings.
"""

import math
import random
from datetime import datetime
from typing import Optional

from app.sensors.base import (
    SensorProvider, SensorReading,
    AccelerometerReading, GyroscopeReading, GPSReading
)
from app.sensors.gps import SimulatedGPSProvider
from app.config import settings

# ── Scenario Definitions ──────────────────────────────────────────────────────
# Each scenario defines (mean, std) for each axis.
# Values in m/s² for accelerometer, deg/s for gyroscope.
# Gravity component (~9.81 m/s²) is included in Z for upright position.

SCENARIO_PROFILES = {
    "NORMAL": {
        "accel": {
            "x": (0.2, 0.15),   # slight forward motion noise
            "y": (0.1, 0.10),   # lateral
            "z": (9.8, 0.15),   # gravity dominant
        },
        "gyro": {
            "x": (1.0, 0.5),
            "y": (0.5, 0.3),
            "z": (1.5, 0.8),
        },
        "alcohol": (0.0, 0.005),
        "speed": (40.0, 5.0),
    },
    "HARD_BRAKING": {
        "accel": {
            "x": (-14.0, 1.5),  # strong deceleration (negative X)
            "y": (0.3, 0.3),
            "z": (9.0, 0.5),
        },
        "gyro": {
            "x": (5.0, 2.0),
            "y": (3.0, 1.5),
            "z": (8.0, 3.0),
        },
        "alcohol": (0.0, 0.005),
        "speed": (10.0, 5.0),
    },
    "SUDDEN_ACCELERATION": {
        "accel": {
            "x": (12.0, 1.5),
            "y": (0.5, 0.3),
            "z": (9.0, 0.5),
        },
        "gyro": {
            "x": (3.0, 1.5),
            "y": (2.0, 1.0),
            "z": (5.0, 2.0),
        },
        "alcohol": (0.0, 0.005),
        "speed": (70.0, 8.0),
    },
    "HIGH_TILT": {
        "accel": {
            "x": (3.0, 1.0),
            "y": (7.0, 1.5),   # high lateral (tilt)
            "z": (6.5, 1.0),
        },
        "gyro": {
            "x": (15.0, 5.0),
            "y": (100.0, 20.0),  # high roll rate
            "z": (50.0, 15.0),
        },
        "alcohol": (0.0, 0.005),
        "speed": (55.0, 10.0),
    },
    "FALL": {
        "accel": {
            "x": (5.0, 2.0),
            "y": (8.0, 2.0),
            "z": (2.0, 1.5),   # Z drops from gravity as helmet tilts to ground
        },
        "gyro": {
            "x": (80.0, 20.0),
            "y": (120.0, 25.0),
            "z": (60.0, 20.0),
        },
        "alcohol": (0.0, 0.005),
        "speed": (5.0, 3.0),
    },
    "ACCIDENT": {
        "accel": {
            "x": (25.0, 3.0),  # high impact X
            "y": (18.0, 3.0),  # high lateral impact
            "z": (4.0, 2.0),   # Z disrupted
        },
        "gyro": {
            "x": (150.0, 30.0),
            "y": (180.0, 35.0),
            "z": (200.0, 40.0),
        },
        "alcohol": (0.0, 0.005),
        "speed": (0.0, 2.0),   # post-impact speed near zero
    },
    "ALCOHOL_DETECTED": {
        "accel": {
            "x": (0.8, 0.4),   # slightly erratic
            "y": (0.6, 0.4),
            "z": (9.5, 0.4),
        },
        "gyro": {
            "x": (5.0, 3.0),
            "y": (4.0, 2.5),
            "z": (6.0, 3.5),
        },
        "alcohol": (0.12, 0.02),  # above legal limit
        "speed": (35.0, 8.0),
    },
}

VALID_SCENARIOS = list(SCENARIO_PROFILES.keys())


class SimulatedSensorProvider(SensorProvider):
    """
    Simulated hardware sensor provider.

    Produces realistic synthetic readings for each named scenario.
    Uses Gaussian distributions around known scenario means.

    Architecture note:
      Replace this class with HardwareSensorProvider to use real
      ESP32 + MPU6050 hardware without changing any detection code.
    """

    def __init__(self, seed: Optional[int] = None):
        self._gps = SimulatedGPSProvider()
        if seed is not None:
            random.seed(seed)

    def _sample(self, mean: float, std: float) -> float:
        return round(random.gauss(mean, std), 4)

    def get_reading(self, scenario: Optional[str] = "NORMAL") -> SensorReading:
        scenario = (scenario or "NORMAL").upper()
        if scenario not in SCENARIO_PROFILES:
            raise ValueError(
                f"Unknown scenario '{scenario}'. "
                f"Valid: {VALID_SCENARIOS}"
            )

        profile = SCENARIO_PROFILES[scenario]
        now = datetime.utcnow()

        accel = AccelerometerReading(
            x=self._sample(*profile["accel"]["x"]),
            y=self._sample(*profile["accel"]["y"]),
            z=self._sample(*profile["accel"]["z"]),
        )
        gyro = GyroscopeReading(
            x=self._sample(*profile["gyro"]["x"]),
            y=self._sample(*profile["gyro"]["y"]),
            z=self._sample(*profile["gyro"]["z"]),
        )
        alcohol = max(0.0, self._sample(*profile["alcohol"]))
        speed = max(0.0, self._sample(*profile["speed"]))
        gps_loc = self._gps.get_location()
        gps_loc.speed = speed

        return SensorReading(
            timestamp=now,
            accelerometer=accel,
            gyroscope=gyro,
            gps=gps_loc,
            alcohol=round(alcohol, 4),
            speed=round(speed, 2),
            scenario=scenario,
        )

    def get_name(self) -> str:
        return "SimulatedSensorProvider [SOFTWARE SIMULATION MODE]"

    @staticmethod
    def get_valid_scenarios() -> list:
        return VALID_SCENARIOS
