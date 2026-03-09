from fastapi import FastAPI
from routes import resume

app = FastAPI()

app.include_router(resume.router, prefix="/resume", tags=["Resume"])

@app.get("/")
def root():
    return {"status": "running"}