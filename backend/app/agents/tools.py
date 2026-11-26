
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


# =========================================================
# 1. ROLE FILTERING
# =========================================================

TITLE_STOPWORDS = {
    "senior", "junior", "lead", "principal",
    "staff", "associate", "entry", "level",
    "remote", "hybrid", "onsite"
}

ROLE_INTENT_WORDS = {
    "engineer", "developer", "scientist",
    "analyst", "researcher", "architect",
    "manager", "designer", "specialist",
    "consultant", "intern"
}


def normalize_title_tokens(title: str) -> set:
    tokens = set(
        re.findall(r"[a-z0-9]+", (title or "").lower())
    )
    return tokens - TITLE_STOPWORDS


def filter_requested_roles(jobs: list, query: str) -> list:
    query_tokens = set(
        re.findall(r"[a-z0-9]+", (query or "").lower())
    )

    has_role_intent = bool(
        query_tokens.intersection(ROLE_INTENT_WORDS)
    )

    if not has_role_intent:
        return jobs

    filtered_jobs = []

    for job in jobs:
        title_tokens = normalize_title_tokens(
            job.get("title", "")
        )

        if title_tokens and title_tokens.issubset(query_tokens):
            filtered_jobs.append(job)

    return filtered_jobs


# =========================================================
# 2. JSON AND JOB HELPERS
# =========================================================

def parse_json_field(value, default=None):
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


def create_candidate_query(
    candidate_skills: list,
    education_text: str,
    candidate_experience: float,
    preferred_roles: list,
    preferred_locations: list,
) -> str:

    return f"""
    Candidate skills: {", ".join(candidate_skills)}
    Education: {education_text}
    Experience: {candidate_experience} years
    Preferred roles: {", ".join(preferred_roles)}
    Preferred locations: {", ".join(preferred_locations)}
    """


def create_job_record(job, semantic_score: float = 0) -> dict:

    return {
        "job_id": job.job_id,
        "title": job.title,
        "company": job.company,
        "location": job.location,
        "description": job.description,
        "required_skills": parse_json_field(
            job.required_skills
        ),
        "experience_required": job.experience_required or 0,
        "employment_type": job.employment_type,
        "salary_min_lpa": job.salary_min_lpa,
        "salary_max_lpa": job.salary_max_lpa,
        "similarity_score": semantic_score,
    }


# =========================================================
# 3. EXTRACT FILTERS FROM NATURAL LANGUAGE
# =========================================================

def extract_search_filters(query: str) -> dict:
    """
    Extract structured job filters from a natural-language query.

    Supported:
        Salary range in LPA
        Minimum / maximum salary
        Minimum / maximum experience
        Experience ranges
        Location
        Remote / hybrid / onsite
        Employment type
    """

    text = query.lower()

    filters = {
        "location": None,
        "min_experience": None,
        "max_experience": None,
        "employment_type": None,
        "min_salary_lpa": None,
        "max_salary_lpa": None,
    }

    # -----------------------------------------------------
    # SALARY RANGE
    # Example: salary between 8 and 15 LPA
    # -----------------------------------------------------

    salary_range = re.search(
        r"(?:between|from)\s*(\d+(?:\.\d+)?)"
        r"\s*(?:and|to|-)\s*(\d+(?:\.\d+)?)"
        r"\s*(?:lpa|lakhs?|lakhs?\s+per\s+annum)",
        text,
    )

    if salary_range:
        filters["min_salary_lpa"] = float(
            salary_range.group(1)
        )
        filters["max_salary_lpa"] = float(
            salary_range.group(2)
        )

    else:
        # Minimum salary
        min_salary = re.search(
            r"(?:at least|minimum|min|above|over|more than|>=)"
            r"\s*(\d+(?:\.\d+)?)\s*"
            r"(?:lpa|lakhs?|lakhs?\s+per\s+annum)",
            text,
        )

        if min_salary:
            filters["min_salary_lpa"] = float(
                min_salary.group(1)
            )

        # Maximum salary
        max_salary = re.search(
            r"(?:at most|maximum|max|up to|below|under|less than|<=)"
            r"\s*(\d+(?:\.\d+)?)\s*"
            r"(?:lpa|lakhs?|lakhs?\s+per\s+annum)",
            text,
        )

        if max_salary:
            filters["max_salary_lpa"] = float(
                max_salary.group(1)
            )

    # -----------------------------------------------------
    # EXPERIENCE RANGE
    # Example: 0-2 years of experience
    # -----------------------------------------------------

    experience_range = re.search(
        r"(\d+(?:\.\d+)?)\s*(?:-|to|and)\s*"
        r"(\d+(?:\.\d+)?)\s*(?:years?|yrs?)",
        text,
    )

    if experience_range:
        filters["min_experience"] = float(
            experience_range.group(1)
        )
        filters["max_experience"] = float(
            experience_range.group(2)
        )

    else:
        min_experience = re.search(
            r"(?:at least|minimum|min|above|over|more than)"
            r"\s*(\d+(?:\.\d+)?)\s*(?:years?|yrs?)",
            text,
        )

        if min_experience:
            filters["min_experience"] = float(
                min_experience.group(1)
            )

        max_experience = re.search(
            r"(?:at most|maximum|max|up to|below|under|less than)"
            r"\s*(\d+(?:\.\d+)?)\s*(?:years?|yrs?)",
            text,
        )

        if max_experience:
            filters["max_experience"] = float(
                max_experience.group(1)
            )

    # -----------------------------------------------------
    # LOCATION
    # -----------------------------------------------------

    if re.search(r"\bremote\b", text):
        filters["location"] = "Remote"

    elif re.search(r"\bhybrid\b", text):
        filters["location"] = "Hybrid"

    elif re.search(r"\b(onsite|on-site|office-based)\b", text):
        filters["location"] = "Onsite"

    else:
        location_match = re.search(
            r"\b(?:in|at|near)\s+"
            r"([a-z][a-z\s-]*?)"
            r"(?=\s+(?:with|for|paying|salary|experience|"
            r"requiring|that|under|over|minimum|maximum|"
            r"at least|at most|full-time|part-time|contract|"
            r"internship)\b|[,!?]|$)",
            text,
        )

        if location_match:
            filters["location"] = (
                location_match.group(1).strip()
            )

    # -----------------------------------------------------
    # EMPLOYMENT TYPE
    # -----------------------------------------------------

    employment_types = {
        "full-time": ["full-time", "full time", "permanent"],
        "part-time": ["part-time", "part time"],
        "contract": ["contract", "contractual"],
        "internship": ["internship", "intern"],
        "freelance": ["freelance"],
    }

    for employment_type, keywords in employment_types.items():
        if any(keyword in text for keyword in keywords):
            filters["employment_type"] = employment_type
            break

    return filters


# =========================================================
# 4. APPLY FILTERS TO RETRIEVED JOBS
# =========================================================

def apply_search_filters(
    jobs: list,
    filters: dict,
) -> list:
    """
    Apply structured filters to retrieved job dictionaries.

    Salary filters use overlapping salary ranges.
    Jobs without salary data are excluded when a
    salary filter is explicitly requested.
    """

    filtered_jobs = []

    for job in jobs:

        # -------------------------------------------------
        # LOCATION FILTER
        # -------------------------------------------------

        requested_location = filters["location"]

        if requested_location:
            job_location = (
                job.get("location") or ""
            ).lower()

            if requested_location.lower() not in job_location:
                continue

        # -------------------------------------------------
        # EXPERIENCE FILTER
        # -------------------------------------------------

        experience = float(
            job.get("experience_required") or 0
        )

        min_exp = filters["min_experience"]
        max_exp = filters["max_experience"]

        if min_exp is not None and experience < min_exp:
            continue

        if max_exp is not None and experience > max_exp:
            continue

        # -------------------------------------------------
        # EMPLOYMENT TYPE FILTER
        # -------------------------------------------------

        requested_type = filters["employment_type"]

        if requested_type:
            actual_type = (
                job.get("employment_type") or ""
            ).lower().replace(" ", "-")

            if actual_type != requested_type:
                continue

        # -------------------------------------------------
        # SALARY FILTER
        # -------------------------------------------------

        min_salary = filters["min_salary_lpa"]
        max_salary = filters["max_salary_lpa"]

        job_min_salary = job.get("salary_min_lpa")
        job_max_salary = job.get("salary_max_lpa")

        salary_filter_requested = (
            min_salary is not None
            or max_salary is not None
        )

        if salary_filter_requested:

            # Do not assume salary for jobs without salary data.
            if (
                job_min_salary is None
                or job_max_salary is None
            ):
                continue

            # Requested minimum salary:
            # Job maximum must reach the requested minimum.
            if (
                min_salary is not None
                and job_max_salary < min_salary
            ):
                continue

            # Requested maximum salary:
            # Job minimum must not exceed the requested maximum.
            if (
                max_salary is not None
                and job_min_salary > max_salary
            ):
                continue

        filtered_jobs.append(job)

    return filtered_jobs


# =========================================================
# 5. SORT FINAL RESULTS
# =========================================================

def sort_and_assign_ranks(jobs: list) -> list:

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


# =========================================================
# 6. CREATE LANGCHAIN TOOLS
# =========================================================

def create_agent_tools(db: Session, candidate_id: int):

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

    preferred_roles = parse_json_field(
        candidate.preferred_roles
    )

    preferred_locations = parse_json_field(
        candidate.preferred_locations
    )

    candidate_experience = float(
        candidate.experience_years or 0
    )

    education = parse_json_field(candidate.education)

    education_text = json.dumps(
        education,
        ensure_ascii=False,
    )

    candidate_query = create_candidate_query(
        candidate_skills=candidate_skills,
        education_text=education_text,
        candidate_experience=candidate_experience,
        preferred_roles=preferred_roles,
        preferred_locations=preferred_locations,
    )

    # =====================================================
    # TOOL 1: GET CANDIDATE PROFILE
    # =====================================================

    @tool
    def get_candidate_profile() -> dict:
        """
        Retrieve the candidate's saved profile.

        Use when the user asks about their skills,
        education, experience, resume or preferences.
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

    # =====================================================
    # TOOL 2: ADVANCED JOB SEARCH
    # =====================================================

    @tool
    def search_jobs(query: str, top_k: int = 5) -> dict:
        """
        Search and recommend jobs using semantic retrieval,
        advanced filters, Cross-Encoder reranking and
        hybrid candidate matching.

        Supports:
            - Job role
            - Location
            - Remote / Hybrid / Onsite
            - Minimum and maximum experience
            - Employment type
            - Salary range in LPA
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
            # STEP 1: Extract structured filters
            # ---------------------------------------------

            filters = extract_search_filters(search_query)

            # ---------------------------------------------
            # STEP 2: FAISS semantic retrieval
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
            # STEP 3: Candidate profile semantic scores
            # ---------------------------------------------

            profile_similarity_results = search_similar_jobs(
                query=candidate_query,
                top_k=50,
            )

            semantic_scores = {
                item["job_id"]: item.get(
                    "similarity_score", 0
                )
                for item in profile_similarity_results
            }

            # ---------------------------------------------
            # STEP 4: Retrieve complete jobs from SQLite
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

            job_records = []

            for item in retrieved_jobs:

                job_id = item["job_id"]
                job = jobs_by_id.get(job_id)

                if not job:
                    continue

                job_record = create_job_record(
                    job=job,
                    semantic_score=semantic_scores.get(
                        job_id, 0
                    ),
                )

                job_records.append(job_record)

            if not job_records:
                return {
                    "message": "No jobs were found in the database.",
                    "jobs": [],
                }

            # ---------------------------------------------
            # STEP 5: Filter requested roles
            # ---------------------------------------------

            role_filtered_jobs = filter_requested_roles(
                jobs=job_records,
                query=search_query,
            )

            # ---------------------------------------------
            # STEP 6: Apply advanced filters
            # ---------------------------------------------

            filtered_jobs = apply_search_filters(
                jobs=role_filtered_jobs,
                filters=filters,
            )

            if not filtered_jobs:
                return {
                    "message": (
                        "No jobs matched all your requested "
                        "role and filter criteria."
                    ),
                    "search_query": search_query,
                    "filters_applied": filters,
                    "jobs": [],
                }

            # ---------------------------------------------
            # STEP 7: Cross-Encoder reranking
            # ---------------------------------------------

            cross_encoder_results = rerank_jobs(
                candidate_query=candidate_query,
                jobs=filtered_jobs,
                top_k=min(20, len(filtered_jobs)),
            )

            if not cross_encoder_results:
                return {
                    "message": "No jobs remained after reranking.",
                    "jobs": [],
                }

            # ---------------------------------------------
            # STEP 8: Hybrid ranking
            # ---------------------------------------------

            ranked_jobs = rank_jobs(
                candidate_skills=candidate_skills,
                candidate_experience=candidate_experience,
                candidate_locations=preferred_locations,
                retrieved_jobs=cross_encoder_results,
                top_k=20,
            )

            # ---------------------------------------------
            # STEP 9: Sort final recommendations
            # ---------------------------------------------

            ranked_jobs = sort_and_assign_ranks(
                ranked_jobs
            )

            final_results = ranked_jobs[:top_k]

            return {
                "message": (
                    f"Found {len(final_results)} matching jobs."
                ),
                "search_query": search_query,
                "total_matches": len(ranked_jobs),
                "filters_applied": filters,
                "ranking_method": (
                    "FAISS + Advanced Filtering + "
                    "Cross-Encoder + Hybrid Ranking"
                ),
                "jobs": final_results,
            }

        except Exception as error:
            logger.exception("Advanced job search failed")

            return {
                "message": "An error occurred while searching for jobs.",
                "error": str(error),
                "jobs": [],
            }

    # =====================================================
    # TOOL 3: EXPLAIN JOB MATCH
    # =====================================================

    @tool
    def explain_job_match(job_id: str) -> dict:
        """
        Explain why a particular job matches the candidate.

        Returns hybrid match score, score breakdown,
        matched skills, missing skills and explanation.
        """

        try:
            job = (
                db.query(Job)
                .filter(Job.job_id == job_id)
                .first()
            )

            if not job:
                return {
                    "message": f"Job {job_id} was not found."
                }

            profile_similarity_results = search_similar_jobs(
                query=candidate_query,
                top_k=50,
            )

            semantic_scores = {
                item["job_id"]: item.get(
                    "similarity_score", 0
                )
                for item in profile_similarity_results
            }

            job_record = create_job_record(
                job=job,
                semantic_score=semantic_scores.get(job_id, 0),
            )

            ranked_results = rank_jobs(
                candidate_skills=candidate_skills,
                candidate_experience=candidate_experience,
                candidate_locations=preferred_locations,
                retrieved_jobs=[job_record],
                top_k=1,
            )

            if not ranked_results:
                return {
                    "message": "Unable to calculate the job match."
                }

            result = ranked_results[0]

            return {
                "job_id": result.get("job_id"),
                "title": result.get("title"),
                "company": result.get("company"),
                "location": result.get("location"),
                "salary_min_lpa": result.get("salary_min_lpa"),
                "salary_max_lpa": result.get("salary_max_lpa"),
                "match_score": result.get("match_score"),
                "score_breakdown": result.get("score_breakdown"),
                "matched_skills": result.get("matched_skills", []),
                "missing_skills": result.get("missing_skills", []),
                "explanation": result.get("explanation"),
            }

        except Exception as error:
            logger.exception("Job match explanation failed")

            return {
                "message": "An error occurred while explaining the job match.",
                "error": str(error),
            }

    return [
        get_candidate_profile,
        search_jobs,
        explain_job_match,
    ]
