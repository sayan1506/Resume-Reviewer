"""
Rate limiter configuration — separated from main.py to avoid circular imports.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request
import os


def get_user_identifier(request: Request) -> str:
    """Use user_id from JWT if available, else fall back to IP."""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        try:
            import jwt
            token = auth_header.split(" ")[1]
            secret = os.getenv("JWT_SECRET", "")
            algorithm = os.getenv("JWT_ALGORITHM", "HS256")
            payload = jwt.decode(token, secret, algorithms=[algorithm])
            return f"user:{payload.get('user_id', 'unknown')}"
        except Exception:
            pass
    return get_remote_address(request)


limiter = Limiter(key_func=get_user_identifier)
