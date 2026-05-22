from pydantic import BaseModel, EmailStr, Field


class UserSignup(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=72)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PasswordResetRequest(BaseModel):
    email: EmailStr


class GoogleAuthRequest(BaseModel):
    code: str = Field(min_length=1, max_length=2048)


class GoogleUserInfo(BaseModel):
    email: EmailStr
    google_id: str
    name: str | None = None
    avatar_url: str | None = None