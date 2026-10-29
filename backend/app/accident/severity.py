"""
Accident Severity Classification Module.

Computes severity level AFTER accident detection confirms an accident.
Severity is kept separate from detection to maintain modularity.

Severity Levels:
  LOW      → Minor incident, check required
  MEDIUM   → Significant impact, assistance advised
  HIGH     → Serious accident, emergency response needed
  CRITICAL → Extreme impact, immediate emergency response

DISCLAIMER:
  This is a SOFTWARE PROTOTYPE severity estimate.
  It does NOT predict real-world injury severity.
  Clinical/medical severity requires validated hardware + medical datasets.
"""

import logging
from dataclasses import dataclass
from typing import Optional

from app.accident.features import Features
from app.accident.sensor_fusion import FusionResult
from app.config import settings

logger = logging.getLogger(__name__)

# Severity score thresholds (0.0–1.0)
SEVERITY_THRESHOLDS = {
    "CRITICAL": 0.85,
    "HIGH": 0.70,
    "MEDIUM": 0.50,
    "LOW": 0.0,    # default
}


@dataclass
class SeverityResult:
    severity: str           # LOW / MEDIUM / HIGH / CRITICAL
    severity_score: float   # 0.0–1.0 composite
    reasoning: str


def calculate_severity(fusion: FusionResult, features: Features) -> SeverityResult:
    """
    Calculate accident severity from fusion result and features.

    Uses a composite severity score combining:
      - Fusion score (primary)
      - Peak acceleration modifier
      - Gyroscope magnitude modifier

    Args:
        fusion: FusionResult from sensor fusion
        features: Extracted features

    Returns:
        SeverityResult with severity level and reasoning
    """
    base = fusion.final_score

    # Modifiers: push severity higher for extreme values
    accel_modifier = min(0.1, (features.peak_acceleration / 100.0) * 0.1)
    gyro_modifier = min(0.05, (features.peak_gyro / 1000.0) * 0.05)

    severity_score = min(1.0, base + accel_modifier + gyro_modifier)
    severity_score = round(severity_score, 4)

    # Determine severity level
    if severity_score >= SEVERITY_THRESHOLDS["CRITICAL"]:
        severity = "CRITICAL"
        reasoning = (
            f"Critical accident: score={severity_score:.3f}, "
            f"impact={features.acceleration_magnitude:.1f} m/s², "
            f"rotation={features.gyro_magnitude:.1f} deg/s"
        )
    elif severity_score >= SEVERITY_THRESHOLDS["HIGH"]:
        severity = "HIGH"
        reasoning = (
            f"High severity: score={severity_score:.3f}, "
            f"impact={features.acceleration_magnitude:.1f} m/s², "
            f"tilt={features.tilt_angle:.1f}°"
        )
    elif severity_score >= SEVERITY_THRESHOLDS["MEDIUM"]:
        severity = "MEDIUM"
        reasoning = (
            f"Medium severity: score={severity_score:.3f}, "
            f"impact={features.acceleration_magnitude:.1f} m/s²"
        )
    else:
        severity = "LOW"
        reasoning = (
            f"Low severity: score={severity_score:.3f}. "
            "Minor incident detected."
        )

    logger.info(
        "Severity | level=%s score=%.3f accel=%.1f gyro=%.1f tilt=%.1f",
        severity, severity_score,
        features.acceleration_magnitude,
        features.gyro_magnitude,
        features.tilt_angle,
    )

    return SeverityResult(
        severity=severity,
        severity_score=severity_score,
        reasoning=reasoning,
    )
