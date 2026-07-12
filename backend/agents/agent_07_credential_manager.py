"""
Agent 07 — Credential & Session Manager
AES-256 encrypted storage of platform credentials.
Handles rate limiting, session persistence, and OAuth token management.
"""
import os
import base64
import json
from datetime import datetime, timedelta
from typing import Optional
from loguru import logger
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from core.config import get_settings

settings = get_settings()

# ─── Rate limits per platform (daily caps from SRS) ───
PLATFORM_RATE_LIMITS = {
    "linkedin": 50,
    "indeed": 100,
    "wellfound": 9999,  # Unlimited via API
    "glassdoor": 30,
    "email": 9999,
}

# ─── In-memory session store (replace with Redis/DB in production) ───
_session_store: dict = {}
_rate_counters: dict = {}  # {user_id: {platform: count}}


def _derive_key(encryption_key: str) -> bytes:
    """Derive a Fernet-compatible key from our hex encryption key."""
    raw = bytes.fromhex(encryption_key[:64]) if len(encryption_key) >= 64 else encryption_key.encode()
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"applymind_salt_2026",
        iterations=100_000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(raw[:32].ljust(32, b"\x00")))
    return key


def _get_fernet() -> Fernet:
    key = _derive_key(settings.encryption_key or "fallback_key_32_bytes_padded_here")
    return Fernet(key)


def encrypt(plaintext: str) -> str:
    """AES-256 encrypt a string. Returns base64-encoded ciphertext."""
    try:
        f = _get_fernet()
        return f.encrypt(plaintext.encode()).decode()
    except Exception as e:
        logger.error(f"[Agent 07] Encryption failed: {e}")
        raise


def decrypt(ciphertext: str) -> str:
    """AES-256 decrypt a string."""
    try:
        f = _get_fernet()
        return f.decrypt(ciphertext.encode()).decode()
    except Exception as e:
        logger.error(f"[Agent 07] Decryption failed: {e}")
        raise


def store_credential(user_id: str, platform: str, username: str, password: str, oauth_token: str = "") -> dict:
    """
    Encrypt and store platform credentials for a user.

    Args:
        user_id: User identifier
        platform: Platform name (linkedin, indeed, wellfound, etc.)
        username: Plaintext username/email
        password: Plaintext password
        oauth_token: Optional OAuth token

    Returns:
        Credential record (encrypted values)
    """
    encrypted_user = encrypt(username)
    encrypted_pass = encrypt(password)
    encrypted_token = encrypt(oauth_token) if oauth_token else ""

    record = {
        "user_id": user_id,
        "platform": platform,
        "encrypted_username": encrypted_user,
        "encrypted_password": encrypted_pass,
        "oauth_token": encrypted_token,
        "token_expires": (datetime.utcnow() + timedelta(days=30)).isoformat(),
        "last_login": None,
        "rate_limit_hits": 0,
        "is_active": True,
        "created_at": datetime.utcnow().isoformat(),
    }

    key = f"{user_id}:{platform}"
    _session_store[key] = record
    logger.info(f"[Agent 07] Stored encrypted credentials for {platform} (user={user_id})")
    return record


def get_credential(user_id: str, platform: str) -> Optional[dict]:
    """Retrieve and decrypt credentials for a platform."""
    key = f"{user_id}:{platform}"
    record = _session_store.get(key)
    if not record:
        return None
    return {
        **record,
        "username": decrypt(record["encrypted_username"]),
        "password": decrypt(record["encrypted_password"]),
        "oauth_token_plain": decrypt(record["oauth_token"]) if record.get("oauth_token") else "",
    }


def check_rate_limit(user_id: str, platform: str) -> dict:
    """
    Check if the user is within the daily rate limit for a platform.

    Returns:
        dict with: allowed (bool), remaining (int), limit (int)
    """
    limit = PLATFORM_RATE_LIMITS.get(platform, 50)
    counter_key = f"{user_id}:{platform}:{datetime.utcnow().date()}"
    current = _rate_counters.get(counter_key, 0)
    remaining = max(0, limit - current)
    return {
        "allowed": current < limit,
        "current": current,
        "remaining": remaining,
        "limit": limit,
        "platform": platform,
    }


def increment_rate_counter(user_id: str, platform: str) -> int:
    """Increment the daily application counter for a platform."""
    counter_key = f"{user_id}:{platform}:{datetime.utcnow().date()}"
    _rate_counters[counter_key] = _rate_counters.get(counter_key, 0) + 1
    return _rate_counters[counter_key]


def record_login(user_id: str, platform: str, success: bool = True):
    """Record a login attempt."""
    key = f"{user_id}:{platform}"
    if key in _session_store:
        _session_store[key]["last_login"] = datetime.utcnow().isoformat()
        if not success:
            _session_store[key]["rate_limit_hits"] = _session_store[key].get("rate_limit_hits", 0) + 1


def get_session_status(user_id: str) -> dict:
    """Get current session status across all platforms for a user."""
    platforms_status = {}
    for platform in PLATFORM_RATE_LIMITS:
        cred = _session_store.get(f"{user_id}:{platform}")
        rate = check_rate_limit(user_id, platform)
        platforms_status[platform] = {
            "has_credentials": cred is not None,
            "is_active": cred.get("is_active", False) if cred else False,
            "rate_limit": rate,
            "last_login": cred.get("last_login") if cred else None,
        }
    return {"user_id": user_id, "platforms": platforms_status}


def run(action: str, user_id: str, platform: str = "", **kwargs) -> dict:
    """
    Main entry point for Agent 07.

    Actions:
        store_cred: Store encrypted credentials
        get_cred: Retrieve decrypted credentials
        check_rate: Check rate limit status
        increment: Increment rate counter
        status: Get full session status
    """
    try:
        if action == "store_cred":
            return store_credential(user_id, platform, kwargs["username"], kwargs["password"], kwargs.get("oauth_token", ""))
        elif action == "get_cred":
            cred = get_credential(user_id, platform)
            return {"status": "success", "credential": cred} if cred else {"status": "not_found"}
        elif action == "check_rate":
            return {"status": "success", **check_rate_limit(user_id, platform)}
        elif action == "increment":
            count = increment_rate_counter(user_id, platform)
            return {"status": "success", "count": count}
        elif action == "status":
            return {"status": "success", **get_session_status(user_id)}
        else:
            return {"status": "error", "message": f"Unknown action: {action}"}
    except Exception as e:
        logger.error(f"[Agent 07] Failed action={action}: {e}")
        return {"status": "error", "message": str(e)}
