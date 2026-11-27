
from collections import Counter
import re


def normalize_skill(skill: str) -> str:
    """
    Normalize skill names for consistent comparison.
    """

    return re.sub(
        r"[^a-z0-9+#.]",
        "",
        skill.lower().strip()
    )


def analyze_skill_gaps(
    candidate_skills: list[str],
    jobs: list[dict],
) -> dict:
    """
    Compare candidate skills against required job skills.

    Returns:
        - Existing skills
        - Missing skills
        - Skill demand frequency
        - Priority levels
        - Skill coverage percentage
    """

    # -------------------------------------------------
    # STEP 1: Normalize candidate skills
    # -------------------------------------------------

    candidate_skill_map = {
        normalize_skill(skill): skill
        for skill in candidate_skills
        if skill.strip()
    }

    candidate_skill_set = set(candidate_skill_map.keys())

    # -------------------------------------------------
    # STEP 2: Collect required skills from jobs
    # -------------------------------------------------

    skill_frequency = Counter()
    skill_labels = {}

    job_analysis = []

    for job in jobs:

        required_skills = job.get("required_skills", [])

        matched_skills = []
        missing_skills = []

        for skill in required_skills:

            normalized = normalize_skill(skill)

            if not normalized:
                continue

            skill_labels.setdefault(normalized, skill)

            if normalized in candidate_skill_set:
                matched_skills.append(skill)
            else:
                missing_skills.append(skill)

            skill_frequency[normalized] += 1

        total_required = len(matched_skills) + len(missing_skills)

        coverage = (
            len(matched_skills) / total_required * 100
            if total_required else 0
        )

        job_analysis.append({
            "job_id": job.get("job_id"),
            "title": job.get("title"),
            "company": job.get("company"),
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "skill_coverage_percentage": round(
                coverage, 2
            ),
        })

    # -------------------------------------------------
    # STEP 3: Identify overall missing skills
    # -------------------------------------------------

    missing_skill_counts = Counter()

    for job in jobs:

        required_skills = job.get("required_skills", [])

        for skill in required_skills:

            normalized = normalize_skill(skill)

            if (
                normalized
                and normalized not in candidate_skill_set
            ):
                missing_skill_counts[normalized] += 1

    # -------------------------------------------------
    # STEP 4: Assign priority levels
    # -------------------------------------------------

    missing_skill_report = []

    for normalized, frequency in missing_skill_counts.items():

        if frequency >= 3:
            priority = "High"

        elif frequency >= 2:
            priority = "Medium"

        else:
            priority = "Low"

        missing_skill_report.append({
            "skill": skill_labels[normalized],
            "demand_count": frequency,
            "priority": priority,
        })

    # Most frequently required skills appear first.
    missing_skill_report.sort(
        key=lambda item: (
            -item["demand_count"],
            item["skill"].lower()
        )
    )

    # -------------------------------------------------
    # STEP 5: Calculate overall skill coverage
    # -------------------------------------------------

    all_required_skills = set(skill_frequency.keys())

    matched_overall = (
        all_required_skills.intersection(candidate_skill_set)
    )

    total_unique_skills = len(all_required_skills)

    overall_coverage = (
        len(matched_overall) / total_unique_skills * 100
        if total_unique_skills else 0
    )

    # -------------------------------------------------
    # STEP 6: Return complete analysis
    # -------------------------------------------------

    return {
        "jobs_analyzed": len(jobs),

        "candidate_skills": candidate_skills,

        "existing_skills": [
            skill_labels.get(skill, original)
            for skill, original in candidate_skill_map.items()
        ],

        "overall_skill_coverage_percentage": round(
            overall_coverage, 2
        ),

        "missing_skills": missing_skill_report,

        "job_wise_analysis": job_analysis,
    }
