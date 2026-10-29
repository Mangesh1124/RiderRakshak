import json
import logging
import smtplib
import time
from datetime import datetime, timedelta
from email.message import EmailMessage

from app.config import settings
from app.services.alert_settings import get_recipients
from app.services.crypto_utils import encrypt_record

logger = logging.getLogger(__name__)
_last_email_time: dict = {}


def alert_email_ready() -> bool:
    return bool(settings.EMAIL_ENABLED and get_recipients())


def should_send_alcohol_email(rider_id: str, alcohol_val: float) -> bool:
    if not alert_email_ready():
        return False
    if alcohol_val < settings.ALCOHOL_ALERT_INDEX:
        return False
    now = time.time()
    if now - _last_email_time.get(rider_id, 0) < settings.EMAIL_COOLDOWN_SECONDS:
        return False
    _last_email_time[rider_id] = now
    return True


def _smtp_send(msg: EmailMessage) -> None:
    if settings.SMTP_PORT == 465:
        with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as s:
            s.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            s.send_message(msg)
    else:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as s:
            s.starttls()
            s.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            s.send_message(msg)


def send_alert_email(event: str, rider_id: str, d: dict) -> None:
    """event: 'ALCOHOL_DETECTED' or 'ACCIDENT_DETECTED'.
    Sensor data is encrypted. The GPS location is readable, and covered by the HMAC."""
    recipients = get_recipients()
    if not recipients or not settings.SMTP_USER:
        logger.warning("Email not sent: no recipients or SMTP_USER not configured")
        return

    ist = datetime.utcnow() + timedelta(hours=5, minutes=30)
    history = d["history"]

    if d["gps_used"]:
        lat, lng = round(d["lat"], 6), round(d["lng"], 6)
        maps = f"https://www.google.com/maps?q={lat},{lng}"
        location_public = {"gps_fix": True, "latitude": lat, "longitude": lng, "maps_link": maps}
        location_text = (
            "Location (not encrypted):\n"
            f"Latitude, Longitude: {lat}, {lng}\n"
            f"Open in Google Maps: {maps}\n"
        )
    else:
        maps = None
        location_public = {"gps_fix": False}
        location_text = "Location: GPS fix not available (location unknown)\n"

    record = {
        "event": event,
        "rider_id": rider_id,
        "captured_at_ist": f"{ist:%Y-%m-%d %H:%M:%S}",
        "trigger_reading": {
            "alcohol_index": round(d["alcohol"], 3),
            "gps_fix": d["gps_used"],
            "latitude": round(d["lat"], 6) if d["gps_used"] else None,
            "longitude": round(d["lng"], 6) if d["gps_used"] else None,
            "maps_link": maps,
            "speed_kmh": round(d["speed"], 1),
            "accel_ms2": {"x": round(d["ax"], 3), "y": round(d["ay"], 3), "z": round(d["az"], 3)},
            "accel_magnitude_ms2": round(d["acc_mag"], 3),
            "gyro_dps": {"x": round(d["gx"], 2), "y": round(d["gy"], 2), "z": round(d["gz"], 2)},
            "tilt_deg": round(d["tilt"], 1),
            "accident_check": {"classification": str(d["classification"]), "score": d["score"]},
        },
        "history": history,
    }
    if event == "ACCIDENT_DETECTED":
        record["accident"] = {"id": d.get("accident_id"), "severity": str(d.get("severity"))}

    try:
        envelope = encrypt_record(record, rider_id, public=location_public)
    except RuntimeError as e:
        # fail closed: never send readings unencrypted
        logger.error("Alert NOT sent: %s", e)
        return
    except Exception:
        logger.exception("Encryption failed, alert not sent")
        return

    stamp = envelope["ts"].replace("-", "").replace(":", "")
    filename = f"riderakshak_alert_{rider_id}_{stamp}.json"

    msg = EmailMessage()
    msg["From"] = settings.EMAIL_FROM or settings.SMTP_USER
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = f"[RideRakshak] Sensor alert - rider {rider_id}"
    msg.set_content(
        "RideRakshak: SENSOR ALERT\n\n"
        f"Rider: {rider_id}\n"
        f"Time (IST): {ist:%d %b %Y, %H:%M:%S}\n\n"
        f"{location_text}\n"
        f"The sensor readings (last {history['window_seconds']} seconds, "
        f"{history['samples']} samples) are encrypted in the attached file.\n"
        f"Format: {envelope['alg']} (encrypt-then-MAC)\n"
        f"Integrity tag (HMAC-SHA256):\n{envelope['hmac']}\n\n"
        f"To verify and read it:  python decrypt_alert.py {filename}\n"
        "You need the shared key. It is never sent by email.\n"
    )
    msg.add_attachment(
        json.dumps(envelope).encode("utf-8"),
        maintype="application", subtype="json", filename=filename,
    )

    try:
        _smtp_send(msg)
        logger.info("%s email sent for %s (%d samples, gps=%s) to %s",
                    event, rider_id, history["samples"], d["gps_used"], recipients)
    except Exception:
        logger.exception("Failed to send alert email")

def send_test_email(recipients: list):
    """Plain test message with no sensor data. Returns (ok, error_text)."""
    if not settings.SMTP_USER:
        return False, "SMTP_USER is not configured on the server"
    msg = EmailMessage()
    msg["Subject"] = "[RideRakshak] Test email"
    msg["From"] = settings.EMAIL_FROM or settings.SMTP_USER
    msg["To"] = ", ".join(recipients)
    msg.set_content(
        "This is a test email from the RideRakshak dashboard.\n"
        "You are set up as an alert receiver."
    )
    try:
        _smtp_send(msg)
        return True, None
    except Exception as e:
        logger.exception("Test email failed")
        return False, f"{type(e).__name__}, see the backend log"