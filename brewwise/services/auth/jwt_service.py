import base64
import hashlib
import hmac
import json
import os
import time
from typing import Optional, Dict, Any
from fastapi import Header, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from brewwise.config import settings
from brewwise.db.session import get_db
from brewwise.models.user import UserModel


def hash_password(password: str) -> tuple[str, str]:
    """Hashes password using PBKDF2-HMAC-SHA256 with random salt."""
    salt = os.urandom(16).hex()
    pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000).hex()
    return pwd_hash, salt


def verify_password(password: str, password_hash: str, salt: str) -> bool:
    """Verifies password against stored PBKDF2 hash and salt."""
    check_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000).hex()
    return hmac.compare_digest(check_hash, password_hash)


def _b64_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64_decode(s: str) -> bytes:
    padding = 4 - (len(s) % 4)
    if padding < 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s)


def create_access_token(user_id: str, email: str, expires_hours: int = 72) -> str:
    """Creates a signed HS256 JWT token."""
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": user_id,
        "email": email,
        "exp": int(time.time()) + (expires_hours * 3600),
        "iat": int(time.time()),
    }

    h_bytes = _b64_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    p_bytes = _b64_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    msg = f"{h_bytes}.{p_bytes}".encode("utf-8")

    sig = hmac.new(settings.SECRET_KEY.encode("utf-8"), msg, hashlib.sha256).digest()
    sig_b64 = _b64_encode(sig)

    return f"{h_bytes}.{p_bytes}.{sig_b64}"


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decodes and cryptographically verifies an HS256 JWT token."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        h_b64, p_b64, sig_b64 = parts

        msg = f"{h_b64}.{p_b64}".encode("utf-8")
        expected_sig = hmac.new(settings.SECRET_KEY.encode("utf-8"), msg, hashlib.sha256).digest()

        actual_sig = _b64_decode(sig_b64)
        if not hmac.compare_digest(expected_sig, actual_sig):
            return None

        payload = json.loads(_b64_decode(p_b64).decode("utf-8"))
        if payload.get("exp", 0) < time.time():
            return None  # Expired

        return payload
    except Exception:
        return None


async def get_current_user_optional(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
) -> Optional[UserModel]:
    """Dependency that returns the current authenticated user or None if anonymous."""
    if not authorization or not authorization.startswith("Bearer "):
        return None

    token = authorization.split("Bearer ")[1].strip()
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        return None

    user_id = payload["sub"]
    stmt = select(UserModel).where(UserModel.id == user_id)
    res = await db.execute(stmt)
    return res.scalar_one_or_none()


async def get_current_user(
    user: Optional[UserModel] = Depends(get_current_user_optional)
) -> UserModel:
    """Dependency that requires an authenticated user (raises 401 otherwise)."""
    if not user:
        raise HTTPException(status_code=401, detail="Authentication credentials required.")
    return user
