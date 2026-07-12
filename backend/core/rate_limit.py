"""
Rate limiting middleware for FastAPI using slowapi.
Provides per-IP and per-user rate limits with Redis backend in production.
Falls back to in-memory storage in development.
"""
import os
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from loguru import logger


def get_user_or_ip(request: Request) -> str:
    """
    Rate limit key: use Firebase UID if token present, else fall back to IP.
    This prevents IP-spoofing bypassing per-user limits.
    """
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        # Use first 16 chars of token as key (not full token — privacy)
        token_prefix = auth_header[7:23]
        return f"user:{token_prefix}"
    return f"ip:{get_remote_address(request)}"


# ─── Storage backend ──────────────────────────────────────────────────
REDIS_URL = os.environ.get("REDIS_URL")

if REDIS_URL:
    storage_uri = REDIS_URL
    logger.info(f"Rate limiter: Redis backend ({REDIS_URL[:30]}...)")
else:
    storage_uri = "memory://"
    logger.warning("Rate limiter: in-memory (dev mode) — use Redis in production")


# ─── Limiter instance ─────────────────────────────────────────────────
limiter = Limiter(
    key_func=get_user_or_ip,
    storage_uri=storage_uri,
    default_limits=["200/minute"],   # global default
)

# Export the error handler so main.py can register it
rate_limit_handler = _rate_limit_exceeded_handler
RateLimitExceededError = RateLimitExceeded


# ─── Rate limit decorators (use these on routes) ──────────────────────
# Usage:
#   @router.post("/login")
#   @limiter.limit("5/minute")
#   async def login(request: Request, ...):
#       ...
#
# Predefined limits for common endpoint groups:
AUTH_LIMIT       = "5/minute"        # login, register
UPLOAD_LIMIT     = "10/hour"         # resume upload
SCRAPE_LIMIT     = "20/hour"         # job scraping (expensive)
APPLY_LIMIT      = "5/hour"          # batch apply (very expensive)
GENERAL_LIMIT    = "60/minute"       # general API calls
REPORT_LIMIT     = "10/hour"         # Groq report generation
