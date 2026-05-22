from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from db.postgres import get_db
from schemas.auth_schema import UserSignup, UserLogin, TokenResponse, GoogleAuthRequest, PasswordResetRequest
from services.auth_service import signup_user, login_user, request_password_reset
from services.oauth_service import exchange_google_code, find_or_create_oauth_user
from utils.jwt_handler import create_access_token
from utils.rate_limiter import limiter

router = APIRouter(prefix="", tags=["Auth"])


@router.post("/signup", response_model=TokenResponse)
def signup(data: UserSignup, db: Session = Depends(get_db)):

    token = signup_user(data.email, data.password, db)

    return {"access_token": token, "token_type": "bearer"}


@router.post("/login", response_model=TokenResponse)
def login(data: UserLogin, db: Session = Depends(get_db)):

    token = login_user(data.email, data.password, db)

    return {"access_token": token, "token_type": "bearer"}


@router.post("/google", response_model=TokenResponse)
@limiter.limit("5/minute")
async def google_auth(
    request: Request,
    data: GoogleAuthRequest,
    db: Session = Depends(get_db),
):
    """Exchange Google authorization code for JWT access token."""
    google_info = await exchange_google_code(data.code)
    user = find_or_create_oauth_user(google_info, db)
    token = create_access_token({"user_id": user.id})
    return {"access_token": token, "token_type": "bearer"}


@router.post("/password-reset")
def password_reset(data: PasswordResetRequest, db: Session = Depends(get_db)):
    """Request a password reset. Rejects OAuth-only users with HTTP 400."""
    result = request_password_reset(data.email, db)
    return result
