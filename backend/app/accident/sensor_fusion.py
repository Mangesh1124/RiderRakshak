"""
Sensor Fusion Module.

Combines evidence from multiple sensors to produce a more reliable
accident determination. Prevents false positives from single-sensor spikes.

Fusion Logic:
  - Single sensor anomaly alone → SUSPICIOUS (score dampened)
  - Multi-sensor corroboration → POSSIBLE or CONFIRMED
  - Alcohol detection → adds advisory flag (not direct score boost)

This module takes a DetectionResult and a Features object,
then applies fusion rules to adjust the classification if needed.

IMPORTANT: Prototype fusion logic. Not experimentally validated.
"""

import logging
from dataclasses import dataclass
from typing import List, Optional

from app.accident.features import Features
from app.accident.threshold_detector import DetectionResult
from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class FusionResult:
    """
    Result after applying sensor fusion to a DetectionResult.
    """
    final_score: float
    final_classification: str
    is_accident: bool
    fusion_notes: List[str]
    original_score: float
    alcohol_detected: bool
    source_detection: DetectionResult

    def to_dict(self) -> dict:
        return {
            "final_score": round(self.final_score, 4),
            "final_classification": self.final_classification,
            "is_accident": self.is_accident,
            "fusion_notes": self.fusion_notes,
            "original_score": round(self.original_score, 4),
            "alcohol_detected": self.alcohol_detected,
        }


def apply_sensor_fusion(detection: DetectionResult, features: Features) -> FusionResult:
    """
    Apply multi-sensor fusion rules to refine accident detection.

    Rules:
      1. If only impact is high but tilt + rotation are low → dampen score
      2. If impact + tilt both exceed threshold → boost score
      3. If impact + rotation both exceed threshold → boost score
      4. Alcohol detected → log advisory (does not increase accident score)
      5. Single-sensor anomaly without corroboration → cap at SUSPICIOUS

    Args:
        detection: Raw detection result from threshold_detector
        features: Extracted features

    Returns:
        FusionResult with adjusted score and classification
    """
    notes = []
    score = detection.accident_score
    breakdown = detection.score_breakdown

    alcohol_detected = features.alcohol >= settings.ALCOHOL_THRESHOLD
    if alcohol_detected:
        notes.append(
            f"ADVISORY: Alcohol detected ({features.alcohol:.3f} >= "
            f"threshold {settings.ALCOHOL_THRESHOLD}). "
            "This is an advisory indicator, not used in accident score."
        )

    # ── Fusion Rule 1: High impact only (no tilt/rotation) → suspicious ───────
    high_impact = features.acceleration_magnitude >= settings.IMPACT_THRESHOLD
    high_tilt = features.tilt_angle >= settings.TILT_THRESHOLD
    high_gyro = features.gyro_magnitude >= settings.GYRO_THRESHOLD
    high_decel = features.deceleration >= settings.DECELERATION_THRESHOLD

    # Count how many sensors are firing
    active_signals = sum([high_impact, high_tilt, high_gyro, high_decel])

    if active_signals == 1 and high_impact:
        # Single spike — could be road bump; dampen
        score *= 0.75
        notes.append(
            "Fusion R1: Only impact signal active. "
            "Dampening score to reduce false positive. "
            f"Adjusted: {score:.3f}"
        )

    # ── Fusion Rule 2: Impact + Tilt → boost ──────────────────────────────────
    if high_impact and high_tilt:
        boost = 0.08
        score = min(1.0, score + boost)
        notes.append(
            f"Fusion R2: High impact + excessive tilt detected. "
            f"Score boosted by {boost}. New: {score:.3f}"
        )

    # ── Fusion Rule 3: Impact + High Rotation → boost ────────────────────────
    if high_impact and high_gyro:
        boost = 0.06
        score = min(1.0, score + boost)
        notes.append(
            f"Fusion R3: High impact + high angular velocity. "
            f"Score boosted by {boost}. New: {score:.3f}"
        )

    # ── Fusion Rule 4: Tilt + Rotation (fall without impact) → possible ───────
    if high_tilt and high_gyro and not high_impact:
        boost = 0.05
        score = min(1.0, score + boost)
        notes.append(
            f"Fusion R4: High tilt + rotation without impact. "
            f"Possible slow fall. Score boosted by {boost}. New: {score:.3f}"
        )

    # ── Fusion Rule 5: Deceleration + Impact → confirm harder braking/crash ───
    if high_decel and high_impact:
        boost = 0.04
        score = min(1.0, score + boost)
        notes.append(
            f"Fusion R5: High deceleration + impact. "
            f"Score boosted by {boost}. New: {score:.3f}"
        )

    # ── Re-classify after fusion ──────────────────────────────────────────────
    score = round(score, 4)

    if score < 0.25:
        classification = "NORMAL"
    elif score < 0.45:
        classification = "SUSPICIOUS"
    elif score < 0.70:
        classification = "POSSIBLE_ACCIDENT"
    else:
        classification = "CONFIRMED_ACCIDENT"

    is_accident = score >= settings.ACCIDENT_SCORE_THRESHOLD

    if not notes:
        notes.append("Fusion: No adjustment rules triggered. Score unchanged.")

    logger.info(
        "Fusion | signals=%d score=%.3f→%.3f class=%s alcohol=%s",
        active_signals,
        detection.accident_score,
        score,
        classification,
        alcohol_detected,
    )

    return FusionResult(
        final_score=score,
        final_classification=classification,
        is_accident=is_accident,
        fusion_notes=notes,
        original_score=detection.accident_score,
        alcohol_detected=alcohol_detected,
        source_detection=detection,
    )
