"""
Emergency Alerts API Routes.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database.models import EmergencyAlert
from app.database.schemas import EmergencyAlertResponse

router = APIRouter(prefix="/api/alerts", tags=["Alerts"])


@router.get("", response_model=list)
def list_alerts(
    limit: int = Query(50, ge=1, le=200),
    skip: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List all emergency alerts."""
    alerts = (
        db.query(EmergencyAlert)
        .order_by(EmergencyAlert.timestamp.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [EmergencyAlertResponse.model_validate(a) for a in alerts]
