"""
Encryption and integrity for RideRakshak sensor records.

Scheme: AES-256-CBC (PKCS7 padding), encrypt-then-MAC with HMAC-SHA256.
Separate encryption and MAC keys are derived from one master key using HKDF-SHA256.
"""
import base64
import hashlib
import hmac
import json
import os
from datetime import datetime, timezone

from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from app.config import settings

VERSION = 1
ALG = "AES-256-CBC+HMAC-SHA256"


def _master_key() -> bytes:
    raw = (settings.EVIDENCE_KEY or "").strip()
    try:
        key = bytes.fromhex(raw)
    except ValueError:
        key = b""
    if len(key) != 32:
        raise RuntimeError("EVIDENCE_KEY must be 64 hex characters (32 bytes)")
    return key


def _derive_keys(master: bytes):
    def hk(info: bytes) -> bytes:
        return HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=info).derive(master)
    return hk(b"riderakshak-enc-v1"), hk(b"riderakshak-mac-v1")


def _canonical(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def _mac(mac_key: bytes, header_bytes: bytes, iv: bytes, ct: bytes) -> bytes:
    msg = len(header_bytes).to_bytes(4, "big") + header_bytes + iv + ct
    return hmac.new(mac_key, msg, hashlib.sha256).digest()


def encrypt_record(record: dict, rider_id: str, public: dict | None = None) -> dict:
    """Encrypts and authenticates a record. `public` stays readable but is covered by the HMAC."""
    enc_key, mac_key = _derive_keys(_master_key())
    header = {
        "v": VERSION,
        "alg": ALG,
        "rider_id": rider_id,
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    if public:
        header["public"] = public
    iv = os.urandom(16)
    padder = padding.PKCS7(128).padder()
    padded = padder.update(_canonical(record)) + padder.finalize()
    encryptor = Cipher(algorithms.AES(enc_key), modes.CBC(iv)).encryptor()
    ct = encryptor.update(padded) + encryptor.finalize()
    tag = _mac(mac_key, _canonical(header), iv, ct)
    return {
        **header,
        "iv": base64.b64encode(iv).decode(),
        "ct": base64.b64encode(ct).decode(),
        "hmac": tag.hex(),
    }


def decrypt_record(env: dict) -> dict:
    """Verifies the HMAC first, then decrypts. Raises ValueError if the record was modified."""
    enc_key, mac_key = _derive_keys(_master_key())
    if env.get("v") != VERSION or env.get("alg") != ALG:
        raise ValueError("Unsupported format")
    header = {k: env[k] for k in ("v", "alg", "rider_id", "ts")}
    if env.get("public") is not None:
        header["public"] = env["public"]
    iv = base64.b64decode(env["iv"])
    ct = base64.b64decode(env["ct"])
    expected = _mac(mac_key, _canonical(header), iv, ct).hex()
    if not hmac.compare_digest(expected, str(env.get("hmac", ""))):
        raise ValueError("HMAC mismatch: record was modified or the key is wrong")
    decryptor = Cipher(algorithms.AES(enc_key), modes.CBC(iv)).decryptor()
    padded = decryptor.update(ct) + decryptor.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    return json.loads(unpadder.update(padded) + unpadder.finalize())