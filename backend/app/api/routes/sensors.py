"""
Sensor History API Routes.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database.database import get_db
from app.database.models import SensorReading
from app.database.schemas import SensorReadingResponse
from app.sensors.simulator import SimulatedSensorProvider, VALID_SCENARIOS

router = APIRouter(prefix="/api/sensors", tags=["Sensors"])
_sim = SimulatedSensorProvider()


@router.get("/latest", response_model=Optional[SensorReadingResponse])
def get_latest_reading(rider_id: str = None, db: Session = Depends(get_db)):
    """Get the most recent sensor reading."""
    query = db.query(SensorReading)
    if rider_id:
        query = query.filter(SensorReading.rider_id == rider_id)
    reading = query.order_by(SensorReading.timestamp.desc()).first()
    if not reading:
        return None
    return SensorReadingResponse.model_validate(reading)


@router.get("/history")
def get_sensor_history(
    rider_id: str = None,
    limit: int = Query(100, ge=1, le=500),
    skip: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Get historical sensor readings."""
    query = db.query(SensorReading)
    if rider_id:
        query = query.filter(SensorReading.rider_id == rider_id)
    total = query.count()
    readings = query.order_by(SensorReading.timestamp.desc()).offset(skip).limit(limit).all()
    return {
        "total": total,
        "readings": [SensorReadingResponse.model_validate(r) for r in readings],
    }
