
import json
import logging
import re

from langchain_core.tools import tool
from sqlalchemy.orm import Session

from app.database.models import Candidate, Job
from app.services.retrieval_service import search_similar_jobs
from app.services.ranking_service import rank_jobs
from app.services.reranker_service import rerank_jobs


logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# 1. Helper functions
# ---------------------------------------------------------

TITLE_STOPWORDS = {
    "senior",
    "junior",
    "lead",
    "principal",
    "staff",
    "associate",
    "entry",
    "level",
    "remote",
    "hybrid",
    "onsite",
}

ROLE_INTENT_WORDS = {
    "engineer",
    "developer",
    "scientist",
    "analyst",
    "researcher",
    "architect",
    "manager",
    "designer",
    "specialist",
    "consultant",
    "intern",
}


def parse_json_field(value, default=None):
    """
    Safely parse JSON fields stored in SQLite.
    """

    if default is None:
        default = []

    if value is None:
        return default

    if isinstance(value, (list, dict)):
        return value

    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return default


def normalize_title_tokens(title: str) -> set:
    """
    Convert a job title into normalized tokens.
    """

    tokens = set(re.findall(r"[a-z0-9]+", (title or "").lower()))

    return tokens - TITLE_STOPWORDS


def filter_requested_roles(jobs: list, query: str) -> list:
    """
    Filter jobs according to explicitly requested job roles.

    Example:
        Query: "Find AI Engineer jobs"

        Only jobs whose titles match the requested role
        will be returned.
    """

    query_tokens = set(
        re.findall(r"[a-z0-9]+", (query or "").lower())
    )

    has_role_intent = bool(query_tokens.intersection(ROLE_INTENT_WORDS))

    # If the user did not specify a recognizable job role,
    # do not restrict the results by title.
    if not has_role_intent:
        return jobs

    filtered_jobs = []

    for job in jobs:
        title_tokens = normalize_title_tokens(job.get("title", ""))

        if title_tokens and title_tokens.issubset(query_tokens):
            filtered_jobs.append(job)

    return filtered_jobs


def sort_and_assign_ranks(jobs: list) -> list:
    """
    Sort jobs by final hybrid match score and assign ranks.
    """

    sorted_jobs = sorted(
        jobs,
        key=lambda job: (
            -float(job.get("match_score", 0)),
            job.get("title", ""),
            job.get("job_id", ""),
        ),
    )

    for index, job in enumerate(sorted_jobs, start=1):
        job["rank"] = index

    return sorted_jobs


def create_candidate_query(
    candidate_skills: list,
    education_text: str,
    candidate_experience: float,
    preferred_roles: list,
    preferred_locations: list,
) -> str:
    """
    Create a consistent candidate representation for
    profile-based semantic retrieval.
    """

    return f"""
    Candidate skills: {", ".join(candidate_skills)}
    Education: {education_text}
    Experience: {candidate_experience} years
    Preferred roles: {", ".join(preferred_roles)}
    Preferred locations: {", ".join(preferred_locations)}
    """


def create_job_record(job, semantic_score: float = 0) -> dict:
    """
    Convert a SQLAlchemy Job object into a dictionary
    compatible with the ranking service.
    """

    return {
        "job_id": job.job_id,
        "title": job.title,
        "company": job.company,
        "location": job.location,
        "description": job.description,
        "required_skills": parse_json_field(job.required_skills),
        "experience_required": job.experience_required,
        "employment_type": job.employment_type,
        "similarity_score": semantic_score,
    }


# ---------------------------------------------------------
# 2. Create tools for the recruitment agent
# ---------------------------------------------------------

def create_agent_tools(db: Session, candidate_id: int):
    """
    Create LangChain tools for a particular candidate.

    Available tools:
        1. get_candidate_profile
        2. search_jobs
        3. explain_job_match
    """

    # -----------------------------------------------------
    # Load candidate from SQLite
    # -----------------------------------------------------

    candidate = (
        db.query(Candidate)
        .filter(Candidate.id == candidate_id)
        .first()
    )

    if not candidate:
        raise ValueError(
            f"Candidate with ID {candidate_id} was not found."
        )

    candidate_skills = parse_json_field(candidate.skills)

    preferred_roles = parse_json_field(candidate.preferred_roles)

    preferred_locations = parse_json_field(
        candidate.preferred_locations
    )

    candidate_experience = float(
        candidate.experience_years or 0
    )

    education = parse_json_field(candidate.education)

    education_text = json.dumps(education, ensure_ascii=False)

    # Create a consistent query for profile-based retrieval.
    candidate_query = create_candidate_query(
        candidate_skills=candidate_skills,
        education_text=education_text,
        candidate_experience=candidate_experience,
        preferred_roles=preferred_roles,
        preferred_locations=preferred_locations,
    )

    # -----------------------------------------------------
    # TOOL 1: Get candidate profile
    # -----------------------------------------------------

    @tool
    def get_candidate_profile() -> dict:
        """
        Retrieve the candidate's saved profile from SQLite.

        Use this tool when the user asks about their
        resume, skills, education, experience, or preferences.
        """

        return {
            "candidate_id": candidate.id,
            "name": candidate.name,
            "email": candidate.email,
            "phone": candidate.phone,
            "education": education,
            "skills": candidate_skills,
            "experience_years": candidate_experience,
            "preferred_roles": preferred_roles,
            "preferred_locations": preferred_locations,
            "resume_filename": candidate.resume_filename,
        }

    # -----------------------------------------------------
    # TOOL 2: Search and recommend jobs
    # -----------------------------------------------------

    @tool
    def search_jobs(query: str, top_k: int = 5) -> dict:
        """
        Search for jobs using the user's query.

        Uses:
            1. FAISS semantic retrieval
            2. Candidate-profile semantic scoring
            3. Requested-role filtering
            4. Cross-Encoder reranking
            5. Hybrid ranking

        Returns the best matching jobs with scores,
        matched skills, missing skills, and explanations.
        """

        try:
            search_query = query.strip()

            if not search_query:
                return {
                    "message": "Please provide a job search query.",
                    "jobs": [],
                }

            top_k = max(1, min(int(top_k), 20))

            # ---------------------------------------------
            # STEP 1: Retrieve jobs using the user's query
            # ---------------------------------------------

            retrieved_jobs = search_similar_jobs(
                query=search_query,
                top_k=50,
            )

            if not retrieved_jobs:
                return {
                    "message": "No matching jobs were found.",
                    "jobs": [],
                }

            # ---------------------------------------------
            # STEP 2: Calculate profile-based semantic scores
            # ---------------------------------------------

            profile_similarity_results = search_similar_jobs(
                query=candidate_query,
                top_k=50,
            )

            semantic_scores = {
                item["job_id"]: item.get("similarity_score", 0)
                for item in profile_similarity_results
            }

            # ---------------------------------------------
            # STEP 3: Retrieve complete job records from SQLite
            # ---------------------------------------------

            retrieved_job_ids = [
                item["job_id"]
                for item in retrieved_jobs
            ]

            jobs_from_db = (
                db.query(Job)
                .filter(Job.job_id.in_(retrieved_job_ids))
                .all()
            )

            jobs_by_id = {
                job.job_id: job
                for job in jobs_from_db
            }

            # Preserve the original FAISS retrieval order.
            job_records = []

            for item in retrieved_jobs:
                job_id = item["job_id"]

                job = jobs_by_id.get(job_id)

                if not job:
                    continue

                # Use the consistent candidate-profile score.
                semantic_score = semantic_scores.get(job_id, 0)

                job_record = create_job_record(
                    job=job,
                    semantic_score=semantic_score,
                )

                job_records.append(job_record)

            if not job_records:
                return {
                    "message": "Retrieved jobs could not be found in the database.",
                    "jobs": [],
                }

            # ---------------------------------------------
            # STEP 4: Filter explicitly requested job roles
            # ---------------------------------------------

            filtered_jobs = filter_requested_roles(
                jobs=job_records,
                query=search_query,
            )

            if not filtered_jobs:
                return {
                    "message": (
                        "No jobs matching the requested role "
                        "were found in the available job dataset."
                    ),
                    "jobs": [],
                }

            # ---------------------------------------------
            # STEP 5: Cross-Encoder reranking
            # ---------------------------------------------

            # The Cross-Encoder evaluates the candidate profile
            # against each retrieved job and selects the most
            # relevant candidates.
            #
            # Keep the Cross-Encoder score separate from the
            # existing 0-100 semantic score.

            cross_encoder_results = rerank_jobs(
                candidate_query=candidate_query,
                jobs=filtered_jobs,
                top_k=min(20, len(filtered_jobs)),
            )

            if not cross_encoder_results:
                return {
                    "message": "No relevant jobs remained after reranking.",
                    "jobs": [],
                }

            # ---------------------------------------------
            # STEP 6: Hybrid ranking
            # ---------------------------------------------

            # Apply the existing hybrid scoring formula:
            #
            # Final Score =
            # 45% Semantic Similarity
            # 25% Skill Match
            # 20% Experience Match
            # 10% Location Match
            #
            # Cross-Encoder reranking selects the candidate
            # pool. Hybrid ranking determines the final order
            # within that pool.

            ranked_jobs = rank_jobs(
                candidate_skills=candidate_skills,
                candidate_experience=candidate_experience,
                candidate_locations=preferred_locations,
                retrieved_jobs=cross_encoder_results,
                top_k=20,
            )

            # ---------------------------------------------
            # STEP 7: Sort and assign final ranks
            # ---------------------------------------------

            ranked_jobs = sort_and_assign_ranks(ranked_jobs)

            final_results = ranked_jobs[:top_k]

            return {
                "message": (
                    f"Found {len(final_results)} matching jobs."
                ),
                "search_query": search_query,
                "total_matches": len(ranked_jobs),
                "ranking_method": (
                    "FAISS Retrieval + Cross-Encoder Reranking "
                    "+ Hybrid Ranking"
                ),
                "jobs": final_results,
            }

        except Exception as error:
            logger.exception("Error while searching jobs")

            return {
                "message": "An error occurred while searching for jobs.",
                "error": str(error),
                "jobs": [],
            }

    # -----------------------------------------------------
    # TOOL 3: Explain an individual job match
    # -----------------------------------------------------

    @tool
    def explain_job_match(job_id: str) -> dict:
        """
        Explain why a particular job matches the candidate.

        Returns:
            - Final hybrid match score
            - Semantic similarity score
            - Skill match score
            - Experience compatibility score
            - Location compatibility score
            - Matched skills
            - Missing skills
            - Explanation
        """

        try:
            # ---------------------------------------------
            # STEP 1: Find the requested job in SQLite
            # ---------------------------------------------

            job = (
                db.query(Job)
                .filter(Job.job_id == job_id)
                .first()
            )

            if not job:
                return {
                    "message": f"Job {job_id} was not found.",
                }

            # ---------------------------------------------
            # STEP 2: Get candidate-profile semantic score
            # ---------------------------------------------

            profile_similarity_results = search_similar_jobs(
                query=candidate_query,
                top_k=50,
            )

            semantic_scores = {
                item["job_id"]: item.get("similarity_score", 0)
                for item in profile_similarity_results
            }

            semantic_score = semantic_scores.get(job_id, 0)

            # ---------------------------------------------
            # STEP 3: Prepare job record
            # ---------------------------------------------

            job_record = create_job_record(
                job=job,
                semantic_score=semantic_score,
            )

            # ---------------------------------------------
            # STEP 4: Calculate hybrid match score
            # ---------------------------------------------

            ranked_results = rank_jobs(
                candidate_skills=candidate_skills,
                candidate_experience=candidate_experience,
                candidate_locations=preferred_locations,
                retrieved_jobs=[job_record],
                top_k=1,
            )

            if not ranked_results:
                return {
                    "message": "Unable to calculate the job match.",
                }

            result = ranked_results[0]

            # ---------------------------------------------
            # STEP 5: Return detailed explanation
            # ---------------------------------------------

            return {
                "job_id": result.get("job_id"),
                "title": result.get("title"),
                "company": result.get("company"),
                "location": result.get("location"),
                "match_score": result.get("match_score"),
                "score_breakdown": result.get("score_breakdown"),
                "matched_skills": result.get("matched_skills", []),
                "missing_skills": result.get("missing_skills", []),
                "explanation": result.get("explanation"),
            }

        except Exception as error:
            logger.exception("Error while explaining job match")

            return {
                "message": "An error occurred while explaining the job match.",
                "error": str(error),
            }

    # -----------------------------------------------------
    # Return all available agent tools
    # -----------------------------------------------------

    return [
        get_candidate_profile,
        search_jobs,
        explain_job_match,
    ]
