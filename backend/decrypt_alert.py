import base64, csv, getpass, hashlib, hmac, json, os, sys

from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


def canonical(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def main():
    args = sys.argv[1:]
    csv_path = None
    if "--csv" in args:
        i = args.index("--csv")
        csv_path = args[i + 1] if i + 1 < len(args) else "history.csv"
        del args[i:i + 2]
    if len(args) != 1:
        print("Usage: python decrypt_alert.py <alert.json> [--csv history.csv]")
        sys.exit(1)

    with open(args[0], encoding="utf-8") as f:
        env = json.load(f)

    key_hex = os.environ.get("RIDERAKSHAK_KEY") or getpass.getpass("Key (64 hex characters): ")
    try:
        master = bytes.fromhex(key_hex.strip())
    except ValueError:
        master = b""
    if len(master) != 32:
        print("The key must be 64 hex characters.")
        sys.exit(1)

    def hk(info):
        return HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=info).derive(master)

    enc_key, mac_key = hk(b"riderakshak-enc-v1"), hk(b"riderakshak-mac-v1")

    if env.get("v") != 1 or env.get("alg") != "AES-256-CBC+HMAC-SHA256":
        print("Unsupported format.")
        sys.exit(1)

    header = {k: env[k] for k in ("v", "alg", "rider_id", "ts")}
    iv = base64.b64decode(env["iv"])
    ct = base64.b64decode(env["ct"])
    hb = canonical(header)
    expected = hmac.new(mac_key, len(hb).to_bytes(4, "big") + hb + iv + ct, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected, str(env.get("hmac", ""))):
        print("HMAC-SHA256: INVALID. The record was modified, or the key is wrong. Not decrypting.")
        sys.exit(2)
    print("HMAC-SHA256: VALID (record has not been modified)")

    decryptor = Cipher(algorithms.AES(enc_key), modes.CBC(iv)).decryptor()
    padded = decryptor.update(ct) + decryptor.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    record = json.loads(unpadder.update(padded) + unpadder.finalize())

    history = record.pop("history", None)
    print(f"\nRider: {env['rider_id']}   Encrypted at (UTC): {env['ts']}\n")
    print(json.dumps(record, indent=2))

    if history:
        cols, rows = history["columns"], history["rows"]
        print(f"\nPrevious {history['window_seconds']} s: {history['samples']} samples\n")
        print("  ".join(c.ljust(10) for c in cols))
        for r in rows:
            print("  ".join(str("" if v is None else v).ljust(10) for v in r))
        if csv_path:
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(cols)
                w.writerows(rows)
            print(f"\nSaved to {csv_path}")


if __name__ == "__main__":
    main()