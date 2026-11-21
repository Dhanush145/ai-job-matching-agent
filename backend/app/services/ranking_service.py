
from typing import Any


# Hybrid ranking weights
SEMANTIC_WEIGHT = 0.45
SKILL_WEIGHT = 0.25
EXPERIENCE_WEIGHT = 0.20
LOCATION_WEIGHT = 0.10


def normalize_skill(skill: str) -> str:
    """Normalize skill names for comparison."""
    return " ".join(skill.casefold().strip().split())


def calculate_skill_score(
    candidate_skills: list[str],
    required_skills: list[str]
) -> dict[str, Any]:
    """
    Calculate skill compatibility using required skills.
    """

    candidate_set = {
        normalize_skill(skill)
        for skill in candidate_skills
    }

    required_set = {
        normalize_skill(skill)
        for skill in required_skills
    }

    if not required_set:
        return {
            "score": 100.0,
            "matched_skills": [],
            "missing_skills": []
        }

    matched = candidate_set.intersection(required_set)
    missing = required_set.difference(candidate_set)

    score = (len(matched) / len(required_set)) * 100

    return {
        "score": round(score, 2),
        "matched_skills": sorted(matched),
        "missing_skills": sorted(missing)
    }


def calculate_experience_score(
    candidate_experience: float,
    required_experience: float
) -> float:
    """
    Calculate experience compatibility.

    Candidates meeting the requirement receive 100.
    Candidates below the requirement receive a proportional score.
    """

    candidate_experience = max(
        0.0, float(candidate_experience or 0)
    )

    required_experience = max(
        0.0, float(required_experience or 0)
    )

    if required_experience == 0:
        return 100.0

    if candidate_experience >= required_experience:
        return 100.0

    score = (
        candidate_experience / required_experience
    ) * 100

    return round(score, 2)


def calculate_location_score(
    candidate_locations: list[str],
    job_location: str
) -> float:
    """
    Calculate location compatibility.

    No location preference means the candidate is open
    to all locations.

    Remote jobs match candidates regardless of their
    preferred physical location.
    """

    preferences = {
        normalize_skill(location)
        for location in candidate_locations
        if location and location.strip()
    }

    job_location = normalize_skill(job_location or "")

    if not preferences:
        return 100.0

    if job_location == "remote":
        return 100.0

    if job_location in preferences:
        return 100.0

    return 0.0


def calculate_semantic_score(
    similarity_score: float
) -> float:
    """
    Convert FAISS cosine similarity into a 0-100 score.
    """

    score = float(similarity_score or 0)

    return round(
        max(0.0, min(100.0, score)),
        2
    )


def calculate_hybrid_score(
    semantic_score: float,
    skill_score: float,
    experience_score: float,
    location_score: float
) -> float:
    """
    Calculate final weighted job compatibility score.
    """

    final_score = (
        semantic_score * SEMANTIC_WEIGHT
        + skill_score * SKILL_WEIGHT
        + experience_score * EXPERIENCE_WEIGHT
        + location_score * LOCATION_WEIGHT
    )

    return round(final_score, 2)


def rank_jobs(
    candidate_skills: list[str],
    candidate_experience: float,
    candidate_locations: list[str],
    retrieved_jobs: list[dict],
    top_k: int = 10
) -> list[dict]:
    """
    Rank retrieved jobs using hybrid scoring.
    """

    ranked_jobs = []

    for job in retrieved_jobs:

        # Calculate semantic similarity
        semantic_score = calculate_semantic_score(
            job.get("similarity_score", 0)
        )

        # Calculate skill compatibility
        skill_result = calculate_skill_score(
            candidate_skills,
            job.get("required_skills", [])
        )

        # Calculate experience compatibility
        experience_score = calculate_experience_score(
            candidate_experience,
            job.get("experience_required", 0)
        )

        # Calculate location compatibility
        location_score = calculate_location_score(
            candidate_locations,
            job.get("location", "")
        )

        # Calculate final weighted score
        final_score = calculate_hybrid_score(
            semantic_score=semantic_score,
            skill_score=skill_result["score"],
            experience_score=experience_score,
            location_score=location_score
        )

        # Generate explanation
        reasons = []

        if skill_result["matched_skills"]:
            reasons.append(
                "Matches skills: "
                + ", ".join(skill_result["matched_skills"])
            )

        if experience_score == 100:
            reasons.append(
                "Meets the required experience level"
            )
        elif experience_score > 0:
            reasons.append(
                "Partially meets the experience requirement"
            )

        if location_score == 100:
            reasons.append(
                "Compatible with location preferences"
            )

        if not reasons:
            reasons.append(
                "Retrieved through semantic job matching"
            )

        # Add ranking information
        ranked_job = {
            **job,

            "match_score": final_score,

            "score_breakdown": {
                "semantic_similarity": semantic_score,
                "skill_matching": skill_result["score"],
                "experience_matching": experience_score,
                "location_matching": location_score
            },

            "matched_skills": skill_result["matched_skills"],

            "missing_skills": skill_result["missing_skills"],

            "explanation": reasons
        }

        ranked_jobs.append(ranked_job)

    # Sort by final hybrid score
    ranked_jobs.sort(
        key=lambda item: item["match_score"],
        reverse=True
    )

    # Assign ranks
    for position, job in enumerate(ranked_jobs, start=1):
        job["rank"] = position

    return ranked_jobs[:top_k]
