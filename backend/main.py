from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from utils.rate_limiter import limiter
from routes import resume, auth
from routes import ai
import os

app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173,https://resume-reviewer-navy.vercel.app"
    ).split(","),
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(resume.router, prefix="/resume", tags=["Resume"])
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(ai.router, prefix="", tags=["AI"])


@app.get("/")
def root():
    return {"status": "running"}
