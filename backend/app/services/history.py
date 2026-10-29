from datetime import timedelta

from sqlalchemy.orm import Session

from app.database.models import SensorReading as SensorReadingModel

COLUMNS = [
    "time_utc", "ax", "ay", "az", "gx", "gy", "gz",
    "acc_mag", "gyro_mag", "tilt_deg", "alcohol", "lat", "lng", "speed_kmh",
]
MAX_ROWS = 600


def _r(v, n):
    return None if v is None else round(float(v), n)


def build_history(db: Session, rider_id: str, scenario: str, end_time, seconds: int) -> dict:
    """Readings of the last `seconds` seconds up to end_time, oldest first."""
    start = end_time - timedelta(seconds=seconds)
    rows = (
        db.query(SensorReadingModel)
        .filter(
            SensorReadingModel.rider_id == rider_id,
            SensorReadingModel.scenario == scenario,
            SensorReadingModel.timestamp >= start,
            SensorReadingModel.timestamp <= end_time,
        )
        .order_by(SensorReadingModel.timestamp.asc())
        .all()
    )[-MAX_ROWS:]

    data = [
        [
            x.timestamp.isoformat(timespec="milliseconds"),
            _r(x.accel_x, 3), _r(x.accel_y, 3), _r(x.accel_z, 3),
            _r(x.gyro_x, 2), _r(x.gyro_y, 2), _r(x.gyro_z, 2),
            _r(x.acceleration_magnitude, 3), _r(x.gyro_magnitude, 2),
            _r(x.tilt_angle, 1), _r(x.alcohol, 3),
            _r(x.latitude, 6), _r(x.longitude, 6), _r(x.speed, 1),
        ]
        for x in rows
    ]
    return {"window_seconds": seconds, "samples": len(data), "columns": COLUMNS, "rows": data}