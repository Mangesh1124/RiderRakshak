import time
from hmac import compare_digest
from typing import Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from app.config import settings
from app.services.crypto_utils import decrypt_record

router = APIRouter(prefix="/api/evidence", tags=["Evidence"])


class Envelope(BaseModel):
    v: int
    alg: str
    rider_id: str
    ts: str
    iv: str
    ct: str
    hmac: str
    public: Optional[dict] = None


def _check_token(token: str) -> None:
    expected = settings.EVIDENCE_ADMIN_TOKEN
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="Decrypt page is disabled: EVIDENCE_ADMIN_TOKEN is not set on the server",
        )
    if not token or not compare_digest(token.encode(), expected.encode()):
        time.sleep(1)  # slows down guessing
        raise HTTPException(status_code=401, detail="Wrong access code")


@router.post("/decrypt")
def decrypt(envelope: Envelope, x_admin_token: str = Header(default="")):
    _check_token(x_admin_token)
    try:
        record = decrypt_record(envelope.model_dump(exclude_none=True))
    except RuntimeError:
        raise HTTPException(status_code=500, detail="EVIDENCE_KEY is not configured on the server")
    except ValueError as e:
        return {"valid": False, "detail": str(e)}
    except Exception:
        return {"valid": False, "detail": "File is corrupted or not a RideRakshak alert"}
    return {
        "valid": True,
        "rider_id": envelope.rider_id,
        "encrypted_at": envelope.ts,
        "public": envelope.public,
        "record": record,
    }