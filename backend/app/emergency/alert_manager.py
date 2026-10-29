"""
Alert Manager — Orchestrates the emergency response pipeline.

Coordinates:
  1. Creating pending accidents
  2. Managing cancellation countdown
  3. Confirming or cancelling accidents
  4. Generating and logging emergency alerts
  5. Database persistence
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.database.models import Accident, EmergencyAlert, Rider
from app.emergency.gsm_simulator import SimulatedGSMAdapter, AlertPayload
from app.config import settings
from app.services.accident_id import generate_accident_id

logger = logging.getLogger(__name__)


def create_pending_accident(
    db: Session,
    rider_id: str,
    accident_score: float,
    classification: str,
    severity: str,
    latitude: float,
    longitude: float,
    sensor_snapshot: dict,
    features_snapshot: dict,
    score_breakdown: dict,
) -> Accident:
    """
    Create a PENDING accident record.
    The cancellation deadline is set to NOW + CANCELLATION_WINDOW_SECONDS.
    """
    accident_id = generate_accident_id(db)
    deadline = datetime.utcnow() + timedelta(
        seconds=settings.CANCELLATION_WINDOW_SECONDS
    )

    accident = Accident(
        id=accident_id,
        rider_id=rider_id,
        timestamp=datetime.utcnow(),
        accident_score=accident_score,
        classification=classification,
        severity=severity,
        status="PENDING",
        cancellation_deadline=deadline,
        latitude=latitude,
        longitude=longitude,
        sensor_snapshot=sensor_snapshot,
        features_snapshot=features_snapshot,
        score_breakdown=score_breakdown,
    )

    db.add(accident)
    db.commit()
    db.refresh(accident)

    logger.info(
        "Pending accident created | id=%s score=%.3f deadline=%s",
        accident_id, accident_score, deadline.isoformat()
    )

    return accident


def confirm_accident(db: Session, accident_id: str) -> Optional[Accident]:
    """
    Confirm a pending accident and trigger emergency alert.
    """
    accident = db.query(Accident).filter(Accident.id == accident_id).first()
    if not accident:
        logger.error("confirm_accident: accident %s not found", accident_id)
        return None

    if accident.status != "PENDING":
        logger.warning(
            "confirm_accident: accident %s already has status=%s",
            accident_id, accident.status
        )
        return accident

    accident.status = "CONFIRMED_ACCIDENT"
    accident.confirmed_at = datetime.utcnow()
    db.commit()

    # Generate emergency alert
    rider = db.query(Rider).filter(Rider.id == accident.rider_id).first()
    emergency_contact = rider.emergency_contact if rider else None

    payload = AlertPayload(
        rider_id=accident.rider_id,
        accident_id=accident.id,
        timestamp=accident.timestamp,
        latitude=accident.latitude or settings.DEFAULT_LATITUDE,
        longitude=accident.longitude or settings.DEFAULT_LONGITUDE,
        severity=accident.severity or "UNKNOWN",
        accident_score=accident.accident_score,
        emergency_contact=emergency_contact,
    )

    gsm = SimulatedGSMAdapter()
    alert_result = gsm.send_alert(payload)

    # Persist alert to database
    alert = EmergencyAlert(
        accident_id=accident.id,
        timestamp=alert_result.timestamp,
        alert_type=alert_result.alert_type,
        status="SIMULATED_SENT",
        recipient=alert_result.recipient,
        message=alert_result.message,
    )
    db.add(alert)
    db.commit()

    logger.info(
        "Accident confirmed | id=%s severity=%s alert_sent=True",
        accident_id, accident.severity
    )

    return accident


def cancel_accident(db: Session, accident_id: str) -> Optional[Accident]:
    """
    Cancel a pending accident (false alert).
    Event is preserved in database with status=FALSE_ALERT_CANCELLED.
    """
    accident = db.query(Accident).filter(Accident.id == accident_id).first()
    if not accident:
        logger.error("cancel_accident: accident %s not found", accident_id)
        return None

    if accident.status != "PENDING":
        logger.warning(
            "cancel_accident: accident %s already has status=%s",
            accident_id, accident.status
        )
        return accident

    accident.status = "FALSE_ALERT_CANCELLED"
    accident.cancelled_at = datetime.utcnow()
    db.commit()

    logger.info("Accident cancelled (false alert) | id=%s", accident_id)

    return accident


def check_and_auto_confirm_expired(db: Session) -> list:
    """
    Check all PENDING accidents past their cancellation deadline
    and auto-confirm them.

    Called periodically by a background task or on API requests.
    """
    now = datetime.utcnow()
    expired = (
        db.query(Accident)
        .filter(
            Accident.status == "PENDING",
            Accident.cancellation_deadline <= now
        )
        .all()
    )

    confirmed_ids = []
    for accident in expired:
        logger.info(
            "Auto-confirming expired pending accident | id=%s deadline=%s",
            accident.id, accident.cancellation_deadline
        )
        confirmed = confirm_accident(db, accident.id)
        if confirmed:
            confirmed_ids.append(confirmed.id)

    return confirmed_ids
