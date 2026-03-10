from fastapi import FastAPI
from routes import resume, auth


app = FastAPI()

app.include_router(resume.router, prefix="/resume", tags=["Resume"])
app.include_router(auth.router, prefix="/auth", tags=["Auth"])

@app.get("/")
def root():
    return {"status": "running"}