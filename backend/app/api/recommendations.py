
import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database.models import Candidate, Job

from app.services.retrieval_service import (
    build_job_index,
    search_similar_jobs
)


# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/recommendations",
    tags=["Recommendations"]
)


def parse_json_list(value, field_name):
    """
    Safely parse JSON database fields into Python lists.
    """

    if not value:
        return []

    try:
        result = json.loads(value)

        if not isinstance(result, list):
            raise ValueError(f"{field_name} must be a list.")

        return result

    except (json.JSONDecodeError, ValueError) as exc:
        raise ValueError(
            f"Invalid data stored in {field_name}: {exc}"
        ) from exc


def format_education(education):
    """
    Convert structured or legacy education records
    into readable text for semantic search.
    """

    education_text = []

    for item in education:

        if isinstance(item, dict):

            details = [
                item.get("degree"),
                item.get("field_of_study"),
                item.get("institution"),
                item.get("graduation_year"),
                item.get("cgpa")
            ]

            formatted = " ".join(
                str(value)
                for value in details
                if value
            )

            if formatted:
                education_text.append(formatted)

        elif isinstance(item, str):

            education_text.append(item)

    return "; ".join(education_text)


@router.post("/index")
def create_index(
    db: Session = Depends(get_db)
):
    """
    Create or rebuild the FAISS job vector index.
    """

    try:
        result = build_job_index(db)

        return result

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )

    except Exception as exc:

        logger.exception("FAISS index creation failed")

        raise HTTPException(
            status_code=500,
            detail="Failed to create job search index."
        ) from exc


@router.get("/{candidate_id}")
def recommend_jobs(
    candidate_id: int,

    top_k: int = Query(
        default=10,
        ge=1,
        le=50
    ),

    db: Session = Depends(get_db)
):
    """
    Generate semantic job recommendations
    for a candidate using FAISS.
    """

    # Step 1: Retrieve candidate
    candidate = db.query(Candidate).filter(
        Candidate.id == candidate_id
    ).first()

    if not candidate:

        raise HTTPException(
            status_code=404,
            detail="Candidate not found."
        )

    try:

        # Step 2: Extract candidate information
        skills = parse_json_list(
            candidate.skills,
            "skills"
        )

        education = parse_json_list(
            candidate.education,
            "education"
        )

        preferred_roles = parse_json_list(
            candidate.preferred_roles,
            "preferred_roles"
        )

        preferred_locations = parse_json_list(
            candidate.preferred_locations,
            "preferred_locations"
        )

        # Step 3: Format education information
        education_text = format_education(
            education
        )

        # Step 4: Construct candidate search query
        candidate_query = f"""
        Candidate Name: {candidate.name or ""}

        Candidate Skills:
        {", ".join(str(skill) for skill in skills)}

        Education:
        {education_text}

        Preferred Job Roles:
        {", ".join(str(role) for role in preferred_roles)}

        Preferred Locations:
        {", ".join(str(location) for location in preferred_locations)}

        Experience:
        {candidate.experience_years or 0} years
        """

        # Step 5: Search FAISS
        retrieved_jobs = search_similar_jobs(
            query=candidate_query,
            top_k=top_k
        )

        # Step 6: Retrieve complete job information
        recommendations = []

        for result in retrieved_jobs:

            job = db.query(Job).filter(
                Job.job_id == result["job_id"]
            ).first()

            if not job:
                continue

            job_skills = parse_json_list(
                job.required_skills,
                "required_skills"
            )

            recommendations.append({

                "job_id": job.job_id,

                "title": job.title,

                "company": job.company,

                "location": job.location,

                "description": job.description,

                "required_skills": job_skills,

                "experience_required": job.experience_required,

                "employment_type": job.employment_type,

                "similarity_score": result["similarity_score"]

            })

        # Step 7: Return recommendations
        return {

            "candidate_id": candidate.id,

            "candidate_name": candidate.name,

            "total_recommendations": len(recommendations),

            "recommendations": recommendations

        }

    except HTTPException:
        raise

    except ValueError as exc:

        logger.exception("Recommendation data validation failed")

        raise HTTPException(
            status_code=400,
            detail=str(exc)
        ) from exc

    except Exception as exc:

        logger.exception(
            "Job recommendation failed for candidate %s",
            candidate_id
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to generate job recommendations. "
                   "Check backend logs for details."
        ) from exc
