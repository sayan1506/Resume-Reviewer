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

    if not verify_password(password, user.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    token = create_access_token({"user_id": user.id})

    return token

