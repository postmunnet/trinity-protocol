from __future__ import annotations
import os
import json
import base64
import hmac
import hashlib
from pathlib import Path
from typing import List


class LocalVault:
    """A simple local secrets vault (demo-grade) for Trinity v0.5.

    WARNING: This is a lightweight mechanism intended for local development
    and demos. It uses HMAC-SHA256-derived keystream + XOR for confidentiality.
    For production use, integrate a proper key management/encryption solution.
    """

    def __init__(self, ai_root: Path):
        self.ai_root = ai_root
        self.secrets_dir = ai_root / ".secrets"
        self.secrets_dir.mkdir(parents=True, exist_ok=True)
        self.key_file = self.secrets_dir / "master.key"
        self._key = self._load_or_create_key()

    # --- internal helpers ---
    def _load_or_create_key(self) -> bytes:
        if self.key_file.exists():
            data = self.key_file.read_bytes()
            return base64.urlsafe_b64decode(data)
        key = os.urandom(32)
        self.key_file.write_bytes(base64.urlsafe_b64encode(key))
        return key

    def _keystream(self, nonce: bytes, key_name: str, length: int) -> bytes:
        out = bytearray()
        counter = 0
        while len(out) < length:
            msg = nonce + key_name.encode("utf-8") + counter.to_bytes(4, "big")
            block = hmac.new(self._key, msg, hashlib.sha256).digest()
            out.extend(block)
            counter += 1
        return bytes(out[:length])

    def _enc(self, key_name: str, plaintext: bytes) -> dict:
        nonce = os.urandom(16)
        ks = self._keystream(nonce, key_name, len(plaintext))
        ct = bytes([a ^ b for a, b in zip(plaintext, ks)])
        return {
            "key": key_name,
            "nonce": base64.urlsafe_b64encode(nonce).decode("ascii"),
            "data": base64.urlsafe_b64encode(ct).decode("ascii"),
        }

    def _dec(self, key_name: str, payload: dict) -> bytes:
        nonce = base64.urlsafe_b64decode(payload["nonce"])  # type: ignore[arg-type]
        ct = base64.urlsafe_b64decode(payload["data"])  # type: ignore[arg-type]
        ks = self._keystream(nonce, key_name, len(ct))
        pt = bytes([a ^ b for a, b in zip(ct, ks)])
        return pt

    def _path_for(self, key_name: str) -> Path:
        safe = key_name.replace("/", "_")
        return self.secrets_dir / f"{safe}.json"

    # --- public API ---
    def set_secret(self, key: str, value: str) -> None:
        payload = self._enc(key, value.encode("utf-8"))
        self._path_for(key).write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def get_secret(self, key: str) -> str | None:
        p = self._path_for(key)
        if not p.exists():
            return None
        data = json.loads(p.read_text(encoding="utf-8"))
        return self._dec(key, data).decode("utf-8")

    def delete_secret(self, key: str) -> bool:
        p = self._path_for(key)
        if p.exists():
            p.unlink()
            return True
        return False

    def list_keys(self) -> List[str]:
        keys: List[str] = []
        for f in self.secrets_dir.glob("*.json"):
            try:
                obj = json.loads(f.read_text(encoding="utf-8"))
                if isinstance(obj, dict) and "key" in obj:
                    keys.append(str(obj["key"]))
            except Exception:
                continue
        return sorted(keys)

