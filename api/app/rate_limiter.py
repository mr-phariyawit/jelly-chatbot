"""
Rate Limiting Middleware
Protects API endpoints from abuse using slowapi
"""

from slowapi import Limiter
from slowapi.util import get_remote_address


def get_client_ip(request):
    """Extract client IP, supporting proxies (Cloud Run X-Forwarded-For)."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return get_remote_address(request)


# Global limiter instance
limiter = Limiter(
    key_func=get_client_ip,
    default_limits=["200/minute"],  # Default: 200 requests/minute per IP
    storage_uri="memory://",  # In-memory storage (suitable for single-instance Cloud Run)
)

# Rate limit presets for different endpoint types
RATE_LIMITS = {
    "webhook": "60/minute",      # LINE webhooks: 60/min per IP
    "chat": "20/minute",         # Chat/LLM endpoints: 20/min per IP
    "upload": "10/minute",       # File uploads: 10/min per IP
    "auth": "10/minute",         # Auth endpoints: 10/min per IP
    "read": "120/minute",        # Read-only endpoints: 120/min per IP
    "admin": "60/minute",        # Admin operations: 60/min per IP
}
