import time
from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import settings
from app.services.alert_settings import get_recipients, set_recipients, clean_recipients
from app.services.email_alert import send_test_email

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])

MAX_RECIPIENTS = 10
_last_test = 0.0


class RecipientsPayload(BaseModel):
    recipients: List[str]


@router.get("/email")
def get_email_settings():
    return {
        "recipients": get_recipients(),
        "email_enabled": settings.EMAIL_ENABLED,
        "sender": settings.EMAIL_FROM or settings.SMTP_USER,
        "alcohol_alert_index": settings.ALCOHOL_ALERT_INDEX,
        "cooldown_seconds": settings.EMAIL_COOLDOWN_SECONDS,
    }


@router.put("/email")
def update_recipients(payload: RecipientsPayload):
    valid, invalid = clean_recipients(payload.recipients)
    if invalid:
        raise HTTPException(status_code=422, detail="Invalid email address: " + ", ".join(invalid))
    if len(valid) > MAX_RECIPIENTS:
        raise HTTPException(status_code=422, detail=f"At most {MAX_RECIPIENTS} receivers are allowed")
    set_recipients(valid)
    return {"recipients": valid}


@router.post("/email/test")
def send_test():
    global _last_test
    if not settings.EMAIL_ENABLED:
        raise HTTPException(status_code=400, detail="EMAIL_ENABLED is false on the server")
    recipients = get_recipients()
    if not recipients:
        raise HTTPException(status_code=400, detail="No receivers saved yet")
    if time.time() - _last_test < 10:
        raise HTTPException(status_code=429, detail="Wait a few seconds before sending another test")
    _last_test = time.time()
    ok, err = send_test_email(recipients)
    if not ok:
        raise HTTPException(status_code=502, detail=err)
    return {"sent_to": recipients}