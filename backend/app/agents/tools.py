
import json
import logging

from langchain_core.tools import tool
from sqlalchemy.orm import Session

from app.database.models import Candidate, Job
from app.services.retrieval_service import search_similar_jobs
from app.services.ranking_service import rank_jobs


logger = logging.getLogger(__name__)


def parse_list(value):
    """Convert a JSON string or list into a Python list."""
    if not value:
        return []

    if isinstance(value, list):
        return value

    try:
        result = json.loads(value)
        return result if isinstance(result, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


def format_education(education):
    """Format education details supporting both strings and dictionaries."""
    education_list = parse_list(education)

    formatted = []

    for item in education_list:
        if isinstance(item, dict):
            degree = item.get("degree", "")
            field = item.get("field_of_study", "")
            institution = item.get("institution", "")
            graduation_year = item.get("graduation_year", "")

            details = " ".join(
                str(value)
                for value in [degree, field, institution, graduation_year]
                if value
            )

            if details:
                formatted.append(details)

        elif isinstance(item, str):
            formatted.append(item)

    return ", ".join(formatted)


def create_agent_tools(db: Session, candidate_id: int):
    """
    Create LangChain tools for a specific candidate.
    These tools use the existing SQLite database,
    FAISS retrieval service, and hybrid ranking service.
    """

    candidate = (
        db.query(Candidate)
        .filter(Candidate.id == candidate_id)
        .first()
    )

    if not candidate:
        raise ValueError(f"Candidate with ID {candidate_id} not found.")

    candidate_skills = parse_list(candidate.skills)
    preferred_roles = parse_list(candidate.preferred_roles)
    preferred_locations = parse_list(candidate.preferred_locations)

    candidate_experience = candidate.experience_years or 0

    education_text = format_education(candidate.education)

    candidate_query = f"""
    Candidate skills: {", ".join(candidate_skills)}
    Education: {education_text}
    Experience: {candidate_experience} years
    Preferred roles: {", ".join(preferred_roles)}
    Preferred locations: {", ".join(preferred_locations)}
    """

    @tool
    def get_candidate_profile() -> str:
        """
        Retrieve the current candidate's profile, including skills,
        education, experience, preferred roles, and locations.
        Use this tool when the candidate asks about their profile.
        """

        profile = {
            "candidate_id": candidate.id,
            "name": candidate.name,
            "email": candidate.email,
            "skills": candidate_skills,
            "education": parse_list(candidate.education),
            "experience_years": candidate_experience,
            "preferred_roles": preferred_roles,
            "preferred_locations": preferred_locations,
        }

        return json.dumps(profile, indent=2, default=str)

    @tool
    def search_jobs(query: str, top_k: int = 5) -> str:
        """
        Search and rank jobs relevant to the candidate's profile
        and the user's query.

        Uses FAISS semantic retrieval followed by hybrid ranking.
        Returns match scores, matched skills, missing skills,
        and recommendation explanations.
        """

        try:
            top_k = max(1, min(top_k, 20))

            search_query = f"""
            {candidate_query}

            User job search request: {query}
            """

            # Step 1: Retrieve semantically similar jobs from FAISS.
            retrieved_jobs = search_similar_jobs(
                query=search_query,
                top_k=50
            )

            if not retrieved_jobs:
                return json.dumps({
                    "message": "No relevant jobs found. Please build the FAISS job index first."
                })

            # Step 2: Retrieve complete job records from SQLite.
            retrieved_job_ids = [
                item["job_id"] for item in retrieved_jobs
            ]

            jobs = (
                db.query(Job)
                .filter(Job.job_id.in_(retrieved_job_ids))
                .all()
            )

            if not jobs:
                return json.dumps({
                    "message": "No matching job records were found in the database."
                })

            # Step 3: Build semantic score lookup.
            semantic_scores = {
                item["job_id"]: item.get("similarity_score", 0)
                for item in retrieved_jobs
            }

            # Step 4: Prepare job records for hybrid ranking.
            job_records = []

            for job in jobs:
                job_records.append({
                    "job_id": job.job_id,
                    "title": job.title,
                    "company": job.company,
                    "location": job.location,
                    "description": job.description,
                    "required_skills": parse_list(job.required_skills),
                    "experience_required": job.experience_required,
                    "employment_type": job.employment_type,
                    "similarity_score": semantic_scores.get(
                        job.job_id, 0
                    ),
                })

            # Step 5: Apply the existing Phase 4 hybrid ranking.
            ranked_jobs = rank_jobs(
                candidate_skills=candidate_skills,
                candidate_experience=candidate_experience,
                preferred_locations=preferred_locations,
                jobs=job_records
            )

            # Step 6: Return the top-ranked recommendations.
            results = ranked_jobs[:top_k]

            return json.dumps({
                "candidate_id": candidate_id,
                "search_query": query,
                "total_results": len(results),
                "recommendations": results
            }, indent=2, default=str)

        except Exception:
            logger.exception("Job search tool failed")

            return json.dumps({
                "error": "Unable to search jobs. Check backend logs."
            })

    @tool
    def explain_job_match(job_id: str) -> str:
        """
        Explain why a particular job matches the candidate.
        Provide its match score, matched skills, missing skills,
        experience compatibility, and recommendation explanation.
        """

        try:
            # Step 1: Find the requested job in SQLite.
            job = (
                db.query(Job)
                .filter(Job.job_id == job_id)
                .first()
            )

            if not job:
                return json.dumps({
                    "error": f"Job {job_id} was not found."
                })

            # Step 2: Retrieve its actual semantic similarity score.
            similarity_results = search_similar_jobs(
                query=candidate_query,
                top_k=50
            )

            semantic_score = next(
                (
                    item.get("similarity_score", 0)
                    for item in similarity_results
                    if item.get("job_id") == job_id
                ),
                0
            )

            # Step 3: Prepare the job for hybrid ranking.
            job_record = {
                "job_id": job.job_id,
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "description": job.description,
                "required_skills": parse_list(job.required_skills),
                "experience_required": job.experience_required,
                "employment_type": job.employment_type,
                "similarity_score": semantic_score,
            }

            # Step 4: Calculate the hybrid match score.
            ranked_result = rank_jobs(
                candidate_skills=candidate_skills,
                candidate_experience=candidate_experience,
                preferred_locations=preferred_locations,
                jobs=[job_record]
            )

            if not ranked_result:
                return json.dumps({
                    "error": "Unable to calculate the job match."
                })

            return json.dumps({
                "candidate_id": candidate_id,
                "job_match": ranked_result[0]
            }, indent=2, default=str)

        except Exception:
            logger.exception("Job explanation tool failed")

            return json.dumps({
                "error": f"Unable to explain the match for {job_id}. Check backend logs."
            })

    return [
        get_candidate_profile,
        search_jobs,
        explain_job_match
    ]
