from fastapi import FastAPI
from routes import resume, auth
from routes import ai



app = FastAPI()

app.include_router(resume.router, prefix="/resume", tags=["Resume"])
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(ai.router, prefix="", tags=["AI"])

@app.get("/")
def root():
    return {"status": "running"}