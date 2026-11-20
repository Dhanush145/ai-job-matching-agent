
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database.database import Base, engine
from app.database import models

from app.api.resume import router as resume_router
from app.api.jobs import router as jobs_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create database tables
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="AI Job Matching & Recommendation Agent",
    description="LLM-powered recruitment and job recommendation system",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(resume_router)
app.include_router(jobs_router)


@app.get("/")
def home():
    return {
        "project": "AI Job Matching Agent",
        "status": "running"
    }


@app.get("/health")
def health():
    return {"status": "healthy"}
