from fastapi import HTTPException
from sqlalchemy.orm import Session
from db.models import User
from utils.security import hash_password, verify_password
from utils.jwt_handler import create_access_token


def signup_user(email: str, password: str, db: Session):

    existing_user = db.query(User).filter(User.email == email).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    hashed_password = hash_password(password)

    user = User(
        email=email,
        password=hashed_password
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"user_id": user.id})

    return token


def login_user(email: str, password: str, db: Session):

    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    if user.password is None:
        raise HTTPException(
            status_code=400,
            detail="This account uses Google sign-in. Please use Google to log in."
        )

    if not verify_password(password, user.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    token = create_access_token({"user_id": user.id})

    return token


def request_password_reset(email: str, db: Session):
    """Handle password reset request with OAuth-only user prevention.

    - If user is OAuth-only (auth_provider="google" and password=NULL), return HTTP 400.
    - If user is a linked account (auth_provider="google" but password is NOT NULL), proceed.
    - If email doesn't match any user, return generic success response (avoid revealing account existence).
    """
    user = db.query(User).filter(User.email == email).first()

    if not user:
        # Return generic response to avoid revealing account existence
        return {"message": "If an account with that email exists, a password reset link has been sent."}

    if user.auth_provider == "google" and user.password is None:
        raise HTTPException(
            status_code=400,
            detail="This account uses Google sign-in. Password reset is not available.",
        )

    # For linked accounts or email-only accounts, proceed with normal password reset flow
    return {"message": "If an account with that email exists, a password reset link has been sent."}
