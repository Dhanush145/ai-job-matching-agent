
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

from app.services.ranking_service import rank_jobs


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/recommendations",
    tags=["Recommendations"]
)


def parse_json_list(value, field_name):
    """
    Safely convert database JSON strings into Python lists.
    """

    if not value:
        return []

    try:
        result = json.loads(value)

        if not isinstance(result, list):
            raise ValueError(
                f"{field_name} must contain a JSON list."
            )

        return result

    except (json.JSONDecodeError, ValueError) as exc:
        raise ValueError(
            f"Invalid stored data in {field_name}: {exc}"
        ) from exc


def format_education(education):
    """
    Convert education records into searchable text.
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
    Create or rebuild the FAISS job index.
    """

    try:
        return build_job_index(db)

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        ) from exc

    except Exception as exc:
        logger.exception("FAISS index creation failed")

        raise HTTPException(
            status_code=500,
            detail="Failed to create FAISS index. "
                   "Check backend logs."
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
    Generate hybrid job recommendations using:

    1. Semantic similarity
    2. Skill matching
    3. Experience compatibility
    4. Location preferences
    """

    # ----------------------------------
    # STEP 1: Retrieve candidate
    # ----------------------------------

    candidate = db.query(Candidate).filter(
        Candidate.id == candidate_id
    ).first()

    if not candidate:
        raise HTTPException(
            status_code=404,
            detail="Candidate not found."
        )

    try:

        # ----------------------------------
        # STEP 2: Extract candidate details
        # ----------------------------------

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

        education_text = format_education(
            education
        )

        candidate_experience = float(
            candidate.experience_years or 0
        )

        # ----------------------------------
        # STEP 3: Create candidate query
        # ----------------------------------

        candidate_query = f"""
        Candidate Name:
        {candidate.name or ""}

        Technical Skills:
        {", ".join(str(skill) for skill in skills)}

        Education:
        {education_text}

        Preferred Job Roles:
        {", ".join(str(role) for role in preferred_roles)}

        Preferred Locations:
        {", ".join(str(location) for location in preferred_locations)}

        Professional Experience:
        {candidate_experience} years
        """

        # ----------------------------------
        # STEP 4: FAISS semantic retrieval
        # ----------------------------------

        retrieval_count = max(
            top_k * 3,
            20
        )

        retrieved_jobs = search_similar_jobs(
            query=candidate_query,
            top_k=retrieval_count
        )

        if not retrieved_jobs:
            return {
                "candidate_id": candidate.id,
                "candidate_name": candidate.name,
                "total_recommendations": 0,
                "recommendations": []
            }

        # ----------------------------------
        # STEP 5: Retrieve complete job data
        # ----------------------------------

        complete_jobs = []

        for result in retrieved_jobs:

            job = db.query(Job).filter(
                Job.job_id == result["job_id"]
            ).first()

            if not job:
                continue

            required_skills = parse_json_list(
                job.required_skills,
                "required_skills"
            )

            complete_jobs.append({

                "job_id": job.job_id,

                "title": job.title,

                "company": job.company,

                "location": job.location,

                "description": job.description,

                "required_skills": required_skills,

                "experience_required": float(
                    job.experience_required or 0
                ),

                "employment_type": job.employment_type,

                "similarity_score": result["similarity_score"]

            })

        # ----------------------------------
        # STEP 6: Hybrid ranking
        # ----------------------------------

        ranked_jobs = rank_jobs(

            candidate_skills=skills,

            candidate_experience=candidate_experience,

            candidate_locations=preferred_locations,

            retrieved_jobs=complete_jobs,

            top_k=top_k

        )

        # ----------------------------------
        # STEP 7: Return final recommendations
        # ----------------------------------

        return {

            "candidate_id": candidate.id,

            "candidate_name": candidate.name,

            "ranking_method": "Hybrid Ranking",

            "ranking_weights": {
                "semantic_similarity": 0.45,
                "skill_matching": 0.25,
                "experience_matching": 0.20,
                "location_matching": 0.10
            },

            "total_recommendations": len(ranked_jobs),

            "recommendations": ranked_jobs

        }

    except HTTPException:
        raise

    except ValueError as exc:

        logger.exception(
            "Invalid candidate or job data"
        )

        raise HTTPException(
            status_code=400,
            detail=str(exc)
        ) from exc

    except Exception as exc:

        logger.exception(
            "Hybrid recommendation failed for candidate %s",
            candidate_id
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to generate hybrid recommendations. "
                   "Check backend logs."
        ) from exc
