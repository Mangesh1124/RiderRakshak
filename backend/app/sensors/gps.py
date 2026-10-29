"""
GPS Provider implementations.

Current: SimulatedGPSProvider
Future:  HardwareGPSProvider (ESP32 + GPS module)
"""

import random
from datetime import datetime
from app.sensors.base import GPSProvider, GPSReading
from app.config import settings


class SimulatedGPSProvider(GPSProvider):
    """
    Simulated GPS provider.
    Returns coordinates near a configurable base location with small drift.

    NOTE: This is SOFTWARE SIMULATION.
    GPS accuracy claims require real hardware testing.
    """

    def __init__(
        self,
        base_lat: float = None,
        base_lon: float = None,
        drift: float = 0.001,
    ):
        self.base_lat = base_lat or settings.DEFAULT_LATITUDE
        self.base_lon = base_lon or settings.DEFAULT_LONGITUDE
        self.drift = drift
        self._seed_offset = 0.0

    def get_location(self) -> GPSReading:
        lat = self.base_lat + random.uniform(-self.drift, self.drift)
        lon = self.base_lon + random.uniform(-self.drift, self.drift)
        return GPSReading(
            latitude=round(lat, 6),
            longitude=round(lon, 6),
            timestamp=datetime.utcnow(),
            speed=0.0,  # speed comes from sensor reading
        )

    def get_name(self) -> str:
        return "SimulatedGPSProvider"

    def get_accident_location(self) -> GPSReading:
        """Return a fixed accident location for reproducibility in tests."""
        return GPSReading(
            latitude=self.base_lat,
            longitude=self.base_lon,
            timestamp=datetime.utcnow(),
            speed=0.0,
        )


# ── Future hardware stub (do NOT fill in until hardware available) ─────────────
class HardwareGPSProvider(GPSProvider):
    """
    Placeholder for future real GPS hardware.
    DO NOT USE — hardware integration pending.
    """

    def __init__(self):
        raise NotImplementedError(
            "HardwareGPSProvider requires physical GPS module. "
            "Use SimulatedGPSProvider for software prototype."
        )

    def get_location(self) -> GPSReading:
        raise NotImplementedError

    def get_name(self) -> str:
        return "HardwareGPSProvider"
