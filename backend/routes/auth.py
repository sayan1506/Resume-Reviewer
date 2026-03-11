from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.postgres import get_db
from schemas.auth_schema import UserSignup, UserLogin, TokenResponse
from services.auth_service import signup_user  #, login_user

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/signup", response_model=TokenResponse)
def signup(data: UserSignup, db: Session = Depends(get_db)):

    token = signup_user(data.email, data.password, db)

    return {
        "access_token": token,
        "token_type": "bearer"
    }


# @router.post("/login", response_model=TokenResponse)
# def login(data: UserLogin, db: Session = Depends(get_db)):

#     token = login_user(data.email, data.password, db)

#     return {
#         "access_token": token
#     }