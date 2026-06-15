from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from utils.rate_limiter import limiter
from utils.oauth_config import validate_oauth_config
from routes import resume, auth, share
from routes import ai
from routes import mock_interview
import os


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Custom rate limit handler that includes Retry-After header (Requirement 8.3)."""
    response = JSONResponse(
        {"detail": "Rate limit exceeded"},
        status_code=429,
    )
    # Add Retry-After header with seconds until the limit resets
    response.headers["Retry-After"] = str(60)
    return response


app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Validate OAuth environment configuration at startup
validate_oauth_config()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.getenv(
            "ALLOWED_ORIGINS",
            "http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173,https://resume-reviewer-navy.vercel.app"
        ).split(",")
        if origin.strip()
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(resume.router, prefix="/resume", tags=["Resume"])
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(ai.router, prefix="", tags=["AI"])
app.include_router(share.router, prefix="", tags=["Share"])
app.include_router(mock_interview.router)


@app.get("/")
def root():
    return {"status": "running"}


@app.get("/health")
def health():
    return {"status": "ok"}
