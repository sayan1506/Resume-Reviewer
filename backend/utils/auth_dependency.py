from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import jwt
import os

from db.postgres import get_db
from db.models import User

ALGORITHM = "HS256"

bearer_scheme = HTTPBearer()


def _get_secret_key() -> str:
    key = os.getenv("JWT_SECRET")
    if not key:
        raise RuntimeError("JWT_SECRET environment variable is not set")
    return key


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    token = credentials.credentials
    secret = _get_secret_key()

    try:
        payload = jwt.decode(token, secret, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")

    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user