
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database.database import Base, engine
from app.database import models

from app.api.resume import router as resume_router
from app.api.jobs import router as jobs_router
from app.api.recommendations import router as recommendation_router
from app.api.agent import router as agent_router


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


# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register API routers
app.include_router(resume_router)
app.include_router(jobs_router)
app.include_router(recommendation_router)
app.include_router(agent_router)


@app.get("/")
def home():
    return {
        "project": "AI Job Matching Agent",
        "status": "running"
    }


@app.get("/health")
def health():
    return {"status": "healthy"}
