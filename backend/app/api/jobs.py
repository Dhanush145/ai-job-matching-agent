
import json
import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database.models import Job
from app.schemas.job import JobCreate


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/jobs", tags=["Jobs"])

BASE_DIR = Path(__file__).resolve().parents[3]
JOBS_FILE = BASE_DIR / "data" / "jobs.json"


def serialize_job(job: Job) -> dict:
    """Convert a SQLAlchemy job object into a JSON-compatible dictionary."""

    return {
        "id": job.id,
        "job_id": job.job_id,
        "title": job.title,
        "company": job.company,
        "location": job.location,
        "description": job.description,
        "required_skills": json.loads(job.required_skills or "[]"),
        "experience_required": job.experience_required,
        "employment_type": job.employment_type,
        "salary_min_lpa": job.salary_min_lpa,
        "salary_max_lpa": job.salary_max_lpa,
    }


@router.post("/seed")
def seed_jobs(db: Session = Depends(get_db)):
    """Load sample jobs from data/jobs.json into SQLite."""

    try:
        with open(JOBS_FILE, "r", encoding="utf-8") as file:
            jobs_data = json.load(file)

        added = 0
        updated = 0

        for item in jobs_data:
            existing = (
                db.query(Job)
                .filter(Job.job_id == item["job_id"])
                .first()
            )

            if existing:
                # Update salary fields for existing sample records.
                # Existing jobs without salary data remain NULL.
                if "salary_min_lpa" in item:
                    existing.salary_min_lpa = item["salary_min_lpa"]

                if "salary_max_lpa" in item:
                    existing.salary_max_lpa = item["salary_max_lpa"]

                updated += 1
                continue

            job = Job(
                job_id=item["job_id"],
                title=item["title"],
                company=item["company"],
                location=item["location"],
                description=item["description"],
                required_skills=json.dumps(
                    item.get("required_skills", [])
                ),
                experience_required=item.get(
                    "experience_required", 0
                ),
                employment_type=item.get(
                    "employment_type", "Full-time"
                ),
                salary_min_lpa=item.get("salary_min_lpa"),
                salary_max_lpa=item.get("salary_max_lpa"),
            )

            db.add(job)
            added += 1

        db.commit()

        return {
            "message": "Job dataset loaded successfully",
            "jobs_added": added,
            "existing_jobs_updated": updated,
        }

    except Exception as error:
        db.rollback()
        logger.exception("Job seeding failed")

        raise HTTPException(
            status_code=500,
            detail="Failed to load job dataset.",
        ) from error


@router.get("/")
def get_jobs(
    title: Optional[str] = None,
    location: Optional[str] = None,
    min_experience: Optional[float] = Query(default=None, ge=0),
    max_experience: Optional[float] = Query(default=None, ge=0),
    employment_type: Optional[str] = None,
    min_salary_lpa: Optional[float] = Query(default=None, ge=0),
    max_salary_lpa: Optional[float] = Query(default=None, ge=0),
    db: Session = Depends(get_db),
):
    """
    Retrieve jobs using optional filters.

    Salary filters use overlapping salary ranges.
    Salary is expressed in Lakhs Per Annum (LPA).
    """

    if (
        min_experience is not None
        and max_experience is not None
        and max_experience < min_experience
    ):
        raise HTTPException(
            status_code=400,
            detail="Maximum experience cannot be less than minimum experience.",
        )

    if (
        min_salary_lpa is not None
        and max_salary_lpa is not None
        and max_salary_lpa < min_salary_lpa
    ):
        raise HTTPException(
            status_code=400,
            detail="Maximum salary cannot be less than minimum salary.",
        )

    query = db.query(Job)

    if title:
        query = query.filter(
            Job.title.ilike(f"%{title.strip()}%")
        )

    if location:
        query = query.filter(
            Job.location.ilike(f"%{location.strip()}%")
        )

    if min_experience is not None:
        query = query.filter(
            Job.experience_required >= min_experience
        )

    if max_experience is not None:
        query = query.filter(
            Job.experience_required <= max_experience
        )

    if employment_type:
        query = query.filter(
            Job.employment_type.ilike(
                employment_type.strip()
            )
        )

    # A job qualifies when its salary range overlaps
    # the requested salary range.
    if min_salary_lpa is not None:
        query = query.filter(
            Job.salary_max_lpa.is_not(None),
            Job.salary_max_lpa >= min_salary_lpa,
        )

    if max_salary_lpa is not None:
        query = query.filter(
            Job.salary_min_lpa.is_not(None),
            Job.salary_min_lpa <= max_salary_lpa,
        )

    jobs = query.order_by(Job.id.asc()).all()

    return {
        "total": len(jobs),
        "filters_applied": {
            "title": title,
            "location": location,
            "min_experience": min_experience,
            "max_experience": max_experience,
            "employment_type": employment_type,
            "min_salary_lpa": min_salary_lpa,
            "max_salary_lpa": max_salary_lpa,
        },
        "jobs": [serialize_job(job) for job in jobs],
    }


@router.post("/")
def create_job(
    job_data: JobCreate,
    db: Session = Depends(get_db),
):
    """Create a new job with optional salary information."""

    existing = (
        db.query(Job)
        .filter(Job.job_id == job_data.job_id)
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Job ID already exists.",
        )

    job = Job(
        job_id=job_data.job_id,
        title=job_data.title,
        company=job_data.company,
        location=job_data.location,
        description=job_data.description,
        required_skills=json.dumps(job_data.required_skills),
        experience_required=job_data.experience_required,
        employment_type=job_data.employment_type,
        salary_min_lpa=job_data.salary_min_lpa,
        salary_max_lpa=job_data.salary_max_lpa,
    )

    try:
        db.add(job)
        db.commit()
        db.refresh(job)

        return {
            "message": "Job created successfully",
            "job": serialize_job(job),
        }

    except Exception as error:
        db.rollback()
        logger.exception("Job creation failed")

        raise HTTPException(
            status_code=500,
            detail="Failed to create job.",
        ) from error
