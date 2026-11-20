
import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database.models import Job
from app.schemas.job import JobCreate


router = APIRouter(prefix="/api/jobs", tags=["Jobs"])

BASE_DIR = Path(__file__).resolve().parents[3]
JOBS_FILE = BASE_DIR / "data" / "jobs.json"


@router.post("/seed")
def seed_jobs(db: Session = Depends(get_db)):
    with open(JOBS_FILE, "r", encoding="utf-8") as file:
        jobs_data = json.load(file)

    added = 0

    for item in jobs_data:
        exists = db.query(Job).filter(
            Job.job_id == item["job_id"]
        ).first()

        if exists:
            continue

        job = Job(
            job_id=item["job_id"],
            title=item["title"],
            company=item["company"],
            location=item["location"],
            description=item["description"],
            required_skills=json.dumps(item["required_skills"]),
            experience_required=item["experience_required"],
            employment_type=item["employment_type"]
        )

        db.add(job)
        added += 1

    db.commit()

    return {
        "message": "Job dataset loaded",
        "jobs_added": added
    }


@router.get("/")
def get_jobs(db: Session = Depends(get_db)):
    jobs = db.query(Job).all()

    return [
        {
            "id": job.id,
            "job_id": job.job_id,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "description": job.description,
            "required_skills": json.loads(
                job.required_skills or "[]"
            ),
            "experience_required": job.experience_required,
            "employment_type": job.employment_type
        }
        for job in jobs
    ]


@router.post("/")
def create_job(
    job_data: JobCreate,
    db: Session = Depends(get_db)
):
    existing = db.query(Job).filter(
        Job.job_id == job_data.job_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Job ID already exists."
        )

    job = Job(
        job_id=job_data.job_id,
        title=job_data.title,
        company=job_data.company,
        location=job_data.location,
        description=job_data.description,
        required_skills=json.dumps(job_data.required_skills),
        experience_required=job_data.experience_required,
        employment_type=job_data.employment_type
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    return {
        "message": "Job created successfully",
        "job_id": job.job_id
    }

