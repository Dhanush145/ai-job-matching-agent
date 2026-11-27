"""
Deterministic personalized learning-roadmap generation.
The roadmap is built from the candidate's actual skill-gap analysis.
Durations are estimates for planning, not guarantees.
"""

from math import ceil


SKILL_GUIDANCE = {
    "pytorch": {
        "focus": "Tensors, autograd, datasets, neural-network layers, training loops, and evaluation.",
        "project": "Build and evaluate a neural-network classifier using PyTorch.",
        "milestone": "Train, validate, and explain a working PyTorch model.",
    },
    "django": {
        "focus": "Django project structure, models, views, serializers, authentication, and REST APIs.",
        "project": "Build a Django REST API with CRUD operations and authentication.",
        "milestone": "Demonstrate a tested REST API.",
    },
    "excel": {
        "focus": "Formulas, lookups, pivot tables, data cleaning, and charts.",
        "project": "Create an Excel dashboard from a structured dataset.",
        "milestone": "Deliver a dashboard with validated calculations and useful insights.",
    },
    "llm": {
        "focus": "Language-model fundamentals, prompting, tokens, inference, and evaluation.",
        "project": "Build a small question-answering application using an LLM.",
        "milestone": "Demonstrate a working LLM application and evaluate its responses.",
    },
    "powerbi": {
        "focus": "Data loading, Power Query, data modelling, DAX, and dashboard design.",
        "project": "Build an interactive Power BI dashboard from a business dataset.",
        "milestone": "Deliver a dashboard with clear KPIs and filters.",
    },
    "restapi": {
        "focus": "HTTP methods, status codes, REST conventions, validation, authentication, and testing.",
        "project": "Design and test a REST API for a job or candidate management app.",
        "milestone": "Provide documented endpoints with successful API tests.",
    },
    "statistics": {
        "focus": "Descriptive statistics, probability, distributions, hypothesis testing, and confidence intervals.",
        "project": "Perform exploratory and statistical analysis on a real dataset.",
        "milestone": "Explain the analysis, assumptions, and conclusions.",
    },
    "transformers": {
        "focus": "Attention, embeddings, positional information, encoder/decoder blocks, and fine-tuning basics.",
        "project": "Fine-tune or adapt a small transformer model for text classification.",
        "milestone": "Compare model performance against a simple baseline.",
    },
}


def _skill_key(skill: str) -> str:
    return "".join(ch for ch in str(skill).lower() if ch.isalnum())


def _guidance_for(skill: str) -> dict:
    return SKILL_GUIDANCE.get(
        _skill_key(skill),
        {
            "focus": f"Learn the fundamentals of {skill}, common workflows, and its use in relevant jobs.",
            "project": f"Build a small portfolio project that demonstrates practical use of {skill}.",
            "milestone": f"Complete a working project and explain the main concepts of {skill}.",
        },
    )


def generate_learning_roadmap(
    candidate_skills: list,
    missing_skills: list,
    jobs_analyzed: int,
    overall_skill_coverage_percentage: float | None = None,
    total_weeks: int = 6,
) -> dict:
    """Build a prioritized weekly roadmap from skill-gap analysis."""
    total_weeks = max(2, min(int(total_weeks), 12))
    normalized = []

    for item in missing_skills or []:
        if isinstance(item, str):
            skill, demand_count, priority = item.strip(), 1, "Low"
        elif isinstance(item, dict):
            skill = str(item.get("skill", "")).strip()
            demand_count = int(item.get("demand_count", 0) or 0)
            priority = str(item.get("priority", "Low")).title()
        else:
            continue

        if not skill or skill.lower() in {
            "string", "none", "null", "n/a", "unknown", "undefined"
        }:
            continue

        if priority not in {"High", "Medium", "Low"}:
            priority = "Low"

        normalized.append({
            "skill": skill,
            "demand_count": demand_count,
            "priority": priority,
        })

    priority_order = {"High": 0, "Medium": 1, "Low": 2}
    normalized.sort(
        key=lambda x: (
            priority_order[x["priority"]],
            -x["demand_count"],
            x["skill"].lower(),
        )
    )

    if not normalized:
        return {
            "message": "No missing skills were returned by the skill-gap analysis. Keep strengthening your existing skills and rerun the analysis as the job dataset changes.",
            "jobs_analyzed": int(jobs_analyzed or 0),
            "candidate_skills": candidate_skills or [],
            "overall_skill_coverage_percentage": overall_skill_coverage_percentage,
            "total_weeks": 0,
            "weekly_plan": [],
        }

    skills_per_week = max(1, ceil(len(normalized) / total_weeks))
    weekly_plan = []

    for start in range(0, len(normalized), skills_per_week):
        week_number = len(weekly_plan) + 1
        week_skills = normalized[start:start + skills_per_week]
        skill_tasks = []

        for item in week_skills:
            guidance = _guidance_for(item["skill"])
            skill_tasks.append({
                **item,
                "learning_focus": guidance["focus"],
                "practical_project": guidance["project"],
                "milestone": guidance["milestone"],
                "estimated_effort": "Approximately 3–5 focused study days",
            })

        weekly_plan.append({
            "week": week_number,
            "theme": " and ".join(x["skill"] for x in week_skills),
            "skills": skill_tasks,
            "weekly_deliverable": "Complete the practical task(s), save the work in a portfolio repository, and write a short README explaining the result.",
        })

    return {
        "message": "Learning roadmap generated from the candidate's retrieved job skill gaps.",
        "jobs_analyzed": int(jobs_analyzed or 0),
        "candidate_skills": candidate_skills or [],
        "overall_skill_coverage_percentage": overall_skill_coverage_percentage,
        "missing_skills_count": len(normalized),
        "total_weeks": len(weekly_plan),
        "priority_method": "Higher priority first, then higher demand_count. Demand reflects only the retrieved jobs used in this analysis.",
        "weekly_plan": weekly_plan,
        "final_milestone": "Complete the portfolio projects, add clear README files, and update your resume with only skills and projects you can confidently demonstrate.",
        "note": "Time estimates are approximate and depend on your current knowledge and weekly study time.",
    }
