import jwt
import os
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()


def create_access_token(data: dict) -> str:
    secret = os.getenv("JWT_SECRET")
    algorithm = os.getenv("JWT_ALGORITHM", "HS256")
    expire_minutes = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

    if not secret:
        raise RuntimeError("JWT_SECRET environment variable is not set")

    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
    payload.update({"exp": expire})

    return jwt.encode(payload, secret, algorithm=algorithm)