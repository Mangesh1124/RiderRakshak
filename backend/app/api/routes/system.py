"""
System Status API Routes.
"""

import time
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database.database import get_db
from app.config import settings
from app.database.schemas import SystemStatus
from app.sensors.simulator import SimulatedSensorProvider

router = APIRouter(prefix="/api/system", tags=["System"])
_start_time = time.time()


@router.get("/status", response_model=SystemStatus)
def system_status(db: Session = Depends(get_db)):
    """Get full system status."""
    try:
        db.execute(text("SELECT 1"))
        db_status = "OK"
    except Exception:
        db_status = "ERROR"

    return SystemStatus(
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.APP_ENV,
        simulation_mode=settings.SIMULATION_MODE,
        database_status=db_status,
        active_rider=settings.DEFAULT_RIDER_ID,
        uptime_seconds=round(time.time() - _start_time, 2),
        timestamp=datetime.utcnow(),
    )


@router.get("/config")
def get_config():
    """Get current threshold configuration (read-only)."""
    return {
        "thresholds": {
            "impact_threshold": settings.IMPACT_THRESHOLD,
            "tilt_threshold": settings.TILT_THRESHOLD,
            "gyro_threshold": settings.GYRO_THRESHOLD,
            "deceleration_threshold": settings.DECELERATION_THRESHOLD,
            "accident_score_threshold": settings.ACCIDENT_SCORE_THRESHOLD,
            "alcohol_threshold": settings.ALCOHOL_THRESHOLD,
        },
        "cancellation_window_seconds": settings.CANCELLATION_WINDOW_SECONDS,
        "simulation_mode": settings.SIMULATION_MODE,
        "note": "PROTOTYPE thresholds — not experimentally validated",
    }
