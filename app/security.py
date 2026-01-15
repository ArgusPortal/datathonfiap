"""
Security Module - API Key Auth + Rate Limiting.
Fase 8: Hardening de Produção.
"""

import hashlib
import logging
import os
import time
from collections import defaultdict
from functools import wraps
from typing import Callable, Dict, Optional, Set

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger("api.security")

# --- Configuration ---
API_KEYS_ENV = os.getenv("API_KEYS", "")  # Comma-separated keys or empty for dev
RATE_LIMIT_RPM = int(os.getenv("RATE_LIMIT_RPM", "60"))
MAX_BODY_BYTES = int(os.getenv("MAX_BODY_BYTES", "262144"))  # 256KB
REQUEST_TIMEOUT_MS = int(os.getenv("REQUEST_TIMEOUT_MS", "3000"))

# Public endpoints (no auth required)
PUBLIC_ENDPOINTS: Set[str] = {"/health", "/docs", "/openapi.json", "/redoc"}


def _parse_api_keys() -> Set[str]:
    """Parse API keys from environment variable."""
    api_keys = os.getenv("API_KEYS", "")
    if not api_keys:
        logger.warning("API_KEYS not set - auth disabled in dev mode")
        return set()
    return {k.strip() for k in api_keys.split(",") if k.strip()}


def _hash_key(key: str) -> str:
    """Hash API key for logging (don't log raw keys)."""
    return hashlib.sha256(key.encode()).hexdigest()[:12]


# --- Rate Limiter (Token Bucket in-memory) ---
class RateLimiter:
    """
    In-memory token bucket rate limiter.
    NOTE: In multi-replica deployments, use Redis for shared state.
    """
    
    def __init__(self, rpm: int = RATE_LIMIT_RPM):
        self.rpm = rpm
        self.tokens_per_second = rpm / 60.0
        self._buckets: Dict[str, Dict] = defaultdict(
            lambda: {"tokens": rpm, "last_update": time.time()}
        )
    
    def _refill(self, bucket: Dict) -> None:
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - bucket["last_update"]
        bucket["tokens"] = min(self.rpm, bucket["tokens"] + elapsed * self.tokens_per_second)
        bucket["last_update"] = now
    
    def allow(self, key: str) -> bool:
        """Check if request is allowed for given key."""
        bucket = self._buckets[key]
        self._refill(bucket)
        
        if bucket["tokens"] >= 1:
            bucket["tokens"] -= 1
            return True
        return False
    
    def get_remaining(self, key: str) -> int:
        """Get remaining tokens for key."""
        bucket = self._buckets[key]
        self._refill(bucket)
        return int(bucket["tokens"])
    
    def reset(self, key: str = None) -> None:
        """Reset bucket(s) - useful for testing."""
        if key:
            if key in self._buckets:
                del self._buckets[key]
        else:
            self._buckets.clear()


# Global rate limiter instance
rate_limiter = RateLimiter()


def _error_response(code: str, message: str, request_id: Optional[str] = None, status: int = 400) -> JSONResponse:
    """Standard error response format."""
    return JSONResponse(
        status_code=status,
        content={
            "error": {
                "code": code,
                "message": message,
                "request_id": request_id,
            }
        },
    )


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Combined security middleware:
    - API Key authentication
    - Rate limiting
    - Request size limiting
    """
    
    def __init__(self, app, api_keys: Set[str] = None):
        super().__init__(app)
        self.api_keys = api_keys if api_keys is not None else _parse_api_keys()
        self.auth_enabled = len(self.api_keys) > 0
    
    async def dispatch(self, request: Request, call_next: Callable):
        request_id = getattr(request.state, "request_id", None)
        path = request.url.path
        
        # Skip auth for public endpoints
        if path in PUBLIC_ENDPOINTS:
            return await call_next(request)
        
        # --- Body size check ---
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_BODY_BYTES:
            logger.warning(f"Request too large: {content_length} bytes", extra={"request_id": request_id})
            return _error_response(
                "PAYLOAD_TOO_LARGE",
                f"Request body exceeds {MAX_BODY_BYTES} bytes limit",
                request_id,
                status=413,
            )
        
        # --- API Key Auth ---
        if self.auth_enabled:
            api_key = request.headers.get("X-API-Key")
            
            if not api_key:
                logger.warning("Missing API key", extra={"request_id": request_id, "path": path})
                return _error_response(
                    "UNAUTHORIZED",
                    "Missing X-API-Key header",
                    request_id,
                    status=401,
                )
            
            if api_key not in self.api_keys:
                logger.warning(f"Invalid API key: {_hash_key(api_key)}", extra={"request_id": request_id})
                return _error_response(
                    "UNAUTHORIZED",
                    "Invalid API key",
                    request_id,
                    status=401,
                )
            
            # --- Rate Limiting (per API key) ---
            if path == "/predict":
                if not rate_limiter.allow(api_key):
                    remaining = rate_limiter.get_remaining(api_key)
                    logger.warning(
                        f"Rate limit exceeded for key {_hash_key(api_key)}",
                        extra={"request_id": request_id, "remaining": remaining},
                    )
                    response = _error_response(
                        "RATE_LIMITED",
                        f"Rate limit exceeded. Limit: {RATE_LIMIT_RPM} requests/minute",
                        request_id,
                        status=429,
                    )
                    response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT_RPM)
                    response.headers["X-RateLimit-Remaining"] = str(remaining)
                    response.headers["Retry-After"] = "60"
                    return response
        
        # Process request
        return await call_next(request)


def validate_api_key(api_key: str) -> bool:
    """Validate an API key against configured keys."""
    keys = _parse_api_keys()
    return api_key in keys if keys else True


def get_rate_limit_headers(api_key: str) -> Dict[str, str]:
    """Get rate limit headers for response."""
    remaining = rate_limiter.get_remaining(api_key)
    return {
        "X-RateLimit-Limit": str(RATE_LIMIT_RPM),
        "X-RateLimit-Remaining": str(remaining),
    }
