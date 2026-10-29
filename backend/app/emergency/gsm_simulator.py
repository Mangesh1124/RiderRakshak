"""
GSM Simulator and Alert Manager.

Since no GSM hardware is available, this module simulates:
  - Emergency SMS generation
  - Alert message formatting
  - Alert logging

IMPORTANT:
  All alerts generated here are SIMULATED.
  No actual SMS is sent.
  Always labeled: "SIMULATED GSM EMERGENCY ALERT"

Future hardware integration:
  Implement GSMHardwareAdapter(GSMAdapter) to send real SMS
  via an AT-command serial interface to a GSM module.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class AlertPayload:
    """Data needed to generate an emergency alert."""
    rider_id: str
    accident_id: str
    timestamp: datetime
    latitude: float
    longitude: float
    severity: str
    accident_score: float
    emergency_contact: Optional[str] = None


@dataclass
class AlertResult:
    """Result of sending/simulating an emergency alert."""
    success: bool
    message: str
    alert_type: str
    recipient: Optional[str]
    timestamp: datetime


class GSMAdapter(ABC):
    """
    Abstract GSM adapter interface.
    Implement this to connect real GSM hardware.
    """

    @abstractmethod
    def send_alert(self, payload: AlertPayload) -> AlertResult:
        """Send emergency alert."""
        ...

    @abstractmethod
    def get_adapter_name(self) -> str:
        ...


class SimulatedGSMAdapter(GSMAdapter):
    """
    Simulated GSM adapter.

    Generates realistic emergency alert messages and logs them.
    Does NOT send any actual SMS.

    Replace with HardwareGSMAdapter when physical GSM module is available.
    """

    def send_alert(self, payload: AlertPayload) -> AlertResult:
        message = self._format_message(payload)

        # Log the simulated alert prominently
        logger.warning("=" * 60)
        logger.warning("SIMULATED GSM EMERGENCY ALERT")
        logger.warning("=" * 60)
        for line in message.split("\n"):
            logger.warning(line)
        logger.warning("=" * 60)

        return AlertResult(
            success=True,
            message=message,
            alert_type="SIMULATED_GSM",
            recipient=payload.emergency_contact or "EMERGENCY_CONTACT_PENDING",
            timestamp=datetime.utcnow(),
        )

    def _format_message(self, payload: AlertPayload) -> str:
        maps_url = (
            f"https://maps.google.com/?q={payload.latitude},{payload.longitude}"
        )
        return (
            f"\n{'='*48}\n"
            f"  ⚠️  SIMULATED GSM EMERGENCY ALERT  ⚠️\n"
            f"{'='*48}\n"
            f"\n"
            f"  ACCIDENT DETECTED — RIDERAKSHAK SYSTEM\n"
            f"\n"
            f"  Rider ID:    {payload.rider_id}\n"
            f"  Accident ID: {payload.accident_id}\n"
            f"  Severity:    {payload.severity}\n"
            f"  Score:       {payload.accident_score:.3f}\n"
            f"\n"
            f"  Time: {payload.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
            f"\n"
            f"  📍 Location:\n"
            f"  Lat: {payload.latitude:.6f}\n"
            f"  Lon: {payload.longitude:.6f}\n"
            f"  Map: {maps_url}\n"
            f"\n"
            f"  Emergency Contact: "
            f"{payload.emergency_contact or 'NOT CONFIGURED'}\n"
            f"\n"
            f"  ─────────────────────────────────────────────────\n"
            f"  NOTE: This is a SIMULATED alert.\n"
            f"  No actual SMS was sent.\n"
            f"  Hardware GSM integration pending.\n"
            f"{'='*48}\n"
        )

    def get_adapter_name(self) -> str:
        return "SimulatedGSMAdapter [NO REAL SMS SENT]"


# ── Future hardware stub ───────────────────────────────────────────────────────
class HardwareGSMAdapter(GSMAdapter):
    """
    Placeholder for real GSM hardware (e.g. SIM800L via ESP32 AT commands).
    DO NOT USE — hardware integration pending.
    """

    def __init__(self):
        raise NotImplementedError(
            "HardwareGSMAdapter requires physical GSM module. "
            "Use SimulatedGSMAdapter for software prototype."
        )

    def send_alert(self, payload: AlertPayload) -> AlertResult:
        raise NotImplementedError

    def get_adapter_name(self) -> str:
        return "HardwareGSMAdapter"
