"""
Threshold-Based Accident Detector.

Implements a transparent, explainable accident detection algorithm
using configurable thresholds. Each contributing factor produces
a weighted score that adds up to an overall accident score.

This serves as the BASELINE detector.
The ML detector (ml_detector.py) can later augment or replace this.

IMPORTANT:
  Thresholds are PROTOTYPE values for software demonstration.
  They are NOT experimentally validated.
  Calibrate with labeled real-world data when hardware is available.

Classifications:
  0.0–0.25  → NORMAL
  0.25–0.45 → SUSPICIOUS
  0.45–0.70 → POSSIBLE_ACCIDENT
  0.70–1.0  → CONFIRMED_ACCIDENT
"""

import logging
from dataclasses import dataclass
from typing import Dict, Tuple

from app.accident.features import Features
from app.config import settings

logger = logging.getLogger(__name__)


# ── Score Weight Definitions ──────────────────────────────────────────────────
# These weights determine how much each factor contributes to the accident score.
# Total weight = 1.0 → accident score is in [0.0, 1.0]
SCORE_WEIGHTS = {
    "impact": 0.35,           # High acceleration magnitude
    "tilt": 0.20,             # Excessive lean angle
    "rotation": 0.20,         # High angular velocity
    "deceleration": 0.15,     # Sudden braking/deceleration
    "speed_context": 0.10,    # Speed-based context modifier
}


@dataclass
class DetectionResult:
    """
    Result from the accident detection pipeline.
    Includes score, classification, and explainability breakdown.
    """
    classification: str         # NORMAL / SUSPICIOUS / POSSIBLE_ACCIDENT / CONFIRMED_ACCIDENT
    accident_score: float       # 0.0–1.0
    score_breakdown: Dict[str, float]
    is_accident: bool
    features: Features

    def to_dict(self) -> dict:
        return {
            "classification": self.classification,
            "accident_score": round(self.accident_score, 4),
            "score_breakdown": {k: round(v, 4) for k, v in self.score_breakdown.items()},
            "is_accident": self.is_accident,
            "features": self.features.to_dict(),
        }


def _classify(score: float) -> str:
    """Map accident score to classification label."""
    if score < 0.25:
        return "NORMAL"
    elif score < 0.45:
        return "SUSPICIOUS"
    elif score < 0.70:
        return "POSSIBLE_ACCIDENT"
    else:
        return "CONFIRMED_ACCIDENT"


def _normalize_to_contribution(value: float, threshold: float, max_factor: float = 3.0) -> float:
    """
    Normalize a sensor value to a [0.0, 1.0] contribution factor.

    - Below threshold → 0.0
    - At threshold → ~0.5
    - At max_factor * threshold → 1.0
    """
    if value <= threshold:
        return 0.0
    excess = value - threshold
    scale = (max_factor - 1.0) * threshold
    return min(1.0, excess / scale)


def detect_accident(features: Features) -> DetectionResult:
    """
    Run the threshold-based accident detection algorithm.

    Args:
        features: Extracted feature vector

    Returns:
        DetectionResult with score, classification, and breakdown
    """
    breakdown: Dict[str, float] = {}

    # ── Impact Score ──────────────────────────────────────────────────────────
    # High acceleration magnitude indicates collision or severe impact.
    # Prototype threshold: 20 m/s² (≈2g)
    impact_contrib = _normalize_to_contribution(
        features.acceleration_magnitude,
        threshold=settings.IMPACT_THRESHOLD,
        max_factor=2.5,
    )
    breakdown["impact"] = round(impact_contrib * SCORE_WEIGHTS["impact"], 4)

    # ── Tilt Score ────────────────────────────────────────────────────────────
    # Excessive lean: >45° = suspicious, >80° = likely fallen
    tilt_contrib = _normalize_to_contribution(
        features.tilt_angle,
        threshold=settings.TILT_THRESHOLD,
        max_factor=2.0,  # 90° = full contribution
    )
    breakdown["tilt"] = round(tilt_contrib * SCORE_WEIGHTS["tilt"], 4)

    # ── Rotation Score ────────────────────────────────────────────────────────
    # High angular velocity during/after impact
    rotation_contrib = _normalize_to_contribution(
        features.gyro_magnitude,
        threshold=settings.GYRO_THRESHOLD,
        max_factor=2.0,
    )
    breakdown["rotation"] = round(rotation_contrib * SCORE_WEIGHTS["rotation"], 4)

    # ── Deceleration Score ────────────────────────────────────────────────────
    # Sudden braking or crash deceleration
    deceleration_contrib = _normalize_to_contribution(
        features.deceleration,
        threshold=settings.DECELERATION_THRESHOLD,
        max_factor=2.0,
    )
    breakdown["deceleration"] = round(deceleration_contrib * SCORE_WEIGHTS["deceleration"], 4)

    # ── Speed Context ─────────────────────────────────────────────────────────
    # Low post-impact speed after high impact → stronger accident signal
    # Normal braking can also reduce speed, so this is a context modifier only
    if features.acceleration_magnitude > settings.IMPACT_THRESHOLD * 0.7:
        speed_norm = max(0.0, 1.0 - features.speed / 100.0)  # 0 km/h = 1.0, 100+ = 0.0
        breakdown["speed_context"] = round(speed_norm * SCORE_WEIGHTS["speed_context"], 4)
    else:
        breakdown["speed_context"] = 0.0

    # ── Total Score ───────────────────────────────────────────────────────────
    accident_score = sum(breakdown.values())
    accident_score = round(min(1.0, max(0.0, accident_score)), 4)

    classification = _classify(accident_score)
    is_accident = accident_score >= settings.ACCIDENT_SCORE_THRESHOLD

    result = DetectionResult(
        classification=classification,
        accident_score=accident_score,
        score_breakdown=breakdown,
        is_accident=is_accident,
        features=features,
    )

    logger.info(
        "Detection | scenario=%s score=%.3f class=%s breakdown=%s",
        features.scenario,
        accident_score,
        classification,
        {k: f"{v:.3f}" for k, v in breakdown.items()},
    )

    return result
