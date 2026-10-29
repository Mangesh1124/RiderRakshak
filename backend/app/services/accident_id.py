"""
Accident ID Generation Service.

Format: RR-ACC-YYYYMMDD-NNNN
Example: RR-ACC-20260925-0001

IDs are unique per day. The sequence resets daily.
"""

import logging
from datetime import datetime
from sqlalchemy.orm import Session
from app.database.models import Accident

logger = logging.getLogger(__name__)


def generate_accident_id(db: Session) -> str:
    """
    Generate a unique accident ID.

    Format: RR-ACC-YYYYMMDD-NNNN
    Sequence number is based on count of accidents created today.
    """
    today = datetime.utcnow().strftime("%Y%m%d")
    prefix = f"RR-ACC-{today}-"

    # Count accidents today to get sequence number
    count = (
        db.query(Accident)
        .filter(Accident.id.like(f"{prefix}%"))
        .count()
    )
    sequence = count + 1
    accident_id = f"{prefix}{sequence:04d}"

    logger.debug("Generated accident ID: %s", accident_id)
    return accident_id
