
from fastapi import FastAPI

app = FastAPI(
    title="AI Job Matching Agent",
    description="AI-powered job recommendation system",
    version="1.0.0"
)

@app.get("/")
def home():
    return {
        "message": "AI Job Matching Agent API is running!",
        "status": "success"
    }

@app.get("/health")
def health():
    return {"status": "healthy"}
