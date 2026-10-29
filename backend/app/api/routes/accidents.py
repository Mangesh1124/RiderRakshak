"""
Accidents API Routes.

GET  /api/accidents          → List all accidents
GET  /api/accidents/{id}     → Get accident by ID
POST /api/accidents/{id}/cancel  → Cancel pending accident (false alert)
POST /api/accidents/{id}/confirm → Confirm pending accident
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database.models import Accident, EmergencyAlert
from app.database.schemas import AccidentResponse, AccidentListResponse, EmergencyAlertResponse
from app.emergency.alert_manager import (
    confirm_accident, cancel_accident, check_and_auto_confirm_expired
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/accidents", tags=["Accidents"])


@router.get("", response_model=AccidentListResponse)
def list_accidents(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    List accident events with optional status filter.
    Also auto-confirms any expired pending accidents.
    """
    # Auto-confirm expired pending accidents
    check_and_auto_confirm_expired(db)

    query = db.query(Accident)
    if status:
        query = query.filter(Accident.status == status.upper())

    total = query.count()
    accidents = query.order_by(Accident.timestamp.desc()).offset(skip).limit(limit).all()

    return AccidentListResponse(
        total=total,
        accidents=[AccidentResponse.model_validate(a) for a in accidents],
    )


@router.get("/{accident_id}", response_model=AccidentResponse)
def get_accident(accident_id: str, db: Session = Depends(get_db)):
    """Get a specific accident by ID."""
    # Auto-confirm expired pending accidents
    check_and_auto_confirm_expired(db)

    accident = db.query(Accident).filter(Accident.id == accident_id).first()
    if not accident:
        raise HTTPException(status_code=404, detail=f"Accident '{accident_id}' not found")
    return AccidentResponse.model_validate(accident)


@router.post("/{accident_id}/cancel", response_model=AccidentResponse)
def cancel_accident_route(accident_id: str, db: Session = Depends(get_db)):
    """
    Cancel a pending accident (rider indicates false alert).
    Event is preserved in database with status=FALSE_ALERT_CANCELLED.
    """
    accident = db.query(Accident).filter(Accident.id == accident_id).first()
    if not accident:
        raise HTTPException(status_code=404, detail=f"Accident '{accident_id}' not found")

    if accident.status != "PENDING":
        raise HTTPException(
            status_code=409,
            detail=f"Accident '{accident_id}' is not pending (status: {accident.status})"
        )

    result = cancel_accident(db, accident_id)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to cancel accident")

    logger.info("Accident cancelled via API | id=%s", accident_id)
    return AccidentResponse.model_validate(result)


@router.post("/{accident_id}/confirm", response_model=AccidentResponse)
def confirm_accident_route(accident_id: str, db: Session = Depends(get_db)):
    """
    Manually confirm a pending accident.
    Triggers emergency alert generation.
    """
    accident = db.query(Accident).filter(Accident.id == accident_id).first()
    if not accident:
        raise HTTPException(status_code=404, detail=f"Accident '{accident_id}' not found")

    if accident.status != "PENDING":
        raise HTTPException(
            status_code=409,
            detail=f"Accident '{accident_id}' is not pending (status: {accident.status})"
        )

    result = confirm_accident(db, accident_id)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to confirm accident")

    logger.info("Accident confirmed via API | id=%s", accident_id)
    return AccidentResponse.model_validate(result)


@router.get("/{accident_id}/alerts", response_model=list)
def get_accident_alerts(accident_id: str, db: Session = Depends(get_db)):
    """Get all emergency alerts for an accident."""
    accident = db.query(Accident).filter(Accident.id == accident_id).first()
    if not accident:
        raise HTTPException(status_code=404, detail=f"Accident '{accident_id}' not found")

    alerts = db.query(EmergencyAlert).filter(
        EmergencyAlert.accident_id == accident_id
    ).all()

    return [EmergencyAlertResponse.model_validate(a) for a in alerts]
