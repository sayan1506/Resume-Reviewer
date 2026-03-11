from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from db.postgres import get_db
from schemas.auth_schema import UserSignup, UserLogin, TokenResponse
from services.auth_service import signup_user  #, login_user

router = APIRouter(prefix="", tags=["Auth"])


@router.post("/signup")
def signup(data: UserSignup, response: Response, db: Session = Depends(get_db)):

    token = signup_user(data.email, data.password, db)

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=False,      # True in production (HTTPS)
        samesite="lax",
        max_age=3600
    )

    return {"message": "User created"}


# @router.post("/login", response_model=TokenResponse)
# def login(data: UserLogin, db: Session = Depends(get_db)):

#     token = login_user(data.email, data.password, db)

#     return {
#         "access_token": token
#     }