import json
import re
import threading
from pathlib import Path
from typing import List, Tuple

from app.config import settings

_PATH = Path(__file__).resolve().parents[2] / "alert_settings.json"
_lock = threading.Lock()
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _env_recipients() -> List[str]:
    return [e.strip().lower() for e in settings.EMAIL_TO.split(",") if e.strip()]


def get_recipients() -> List[str]:
    with _lock:
        try:
            data = json.loads(_PATH.read_text(encoding="utf-8"))
            items = data.get("recipients")
            if isinstance(items, list):
                return [str(e) for e in items]
        except (FileNotFoundError, ValueError):
            pass
    return _env_recipients()


def clean_recipients(items: List[str]) -> Tuple[List[str], List[str]]:
    """Returns (valid, invalid). Lowercases, trims and removes duplicates."""
    valid, invalid, seen = [], [], set()
    for raw in items:
        e = (raw or "").strip().lower()
        if not e:
            continue
        if not _EMAIL_RE.match(e) or len(e) > 254:
            invalid.append(raw)
        elif e not in seen:
            seen.add(e)
            valid.append(e)
    return valid, invalid


def set_recipients(recipients: List[str]) -> None:
    tmp = _PATH.with_suffix(".tmp")
    with _lock:
        tmp.write_text(json.dumps({"recipients": recipients}, indent=2), encoding="utf-8")
        tmp.replace(_PATH)