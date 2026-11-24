
import logging

from sentence_transformers import CrossEncoder


logger = logging.getLogger(__name__)

# Cross-encoder model
MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"

# Load the model once when this module is imported.
reranker_model = CrossEncoder(MODEL_NAME)


def create_job_text(job: dict) -> str:
    """
    Convert a job record into text for cross-encoder comparison.
    """

    required_skills = job.get("required_skills", [])

    if isinstance(required_skills, list):
        skills_text = ", ".join(required_skills)
    else:
        skills_text = str(required_skills)

    return f"""
    Job Title: {job.get('title', '')}
    Company: {job.get('company', '')}
    Location: {job.get('location', '')}
    Description: {job.get('description', '')}
    Required Skills: {skills_text}
    Required Experience: {job.get('experience_required', 0)} years
    Employment Type: {job.get('employment_type', '')}
    """


def rerank_jobs(
    candidate_query: str,
    jobs: list[dict],
    top_k: int = 20
) -> list[dict]:
    """
    Rerank retrieved jobs using a cross-encoder.

    The model evaluates the candidate profile and each
    job together instead of comparing independent embeddings.

    Original FAISS similarity scores are preserved.
    """

    if not jobs:
        return []

    top_k = max(1, min(top_k, len(jobs)))

    try:
        # Prepare candidate-job text pairs.
        pairs = []

        for job in jobs:
            job_text = create_job_text(job)

            pairs.append([
                candidate_query,
                job_text
            ])

        # Calculate cross-encoder relevance scores.
        scores = reranker_model.predict(
            pairs,
            show_progress_bar=False
        )

        # Attach cross-encoder scores.
        reranked_jobs = []

        for job, score in zip(jobs, scores):
            updated_job = job.copy()

            updated_job["cross_encoder_score"] = round(
                float(score), 4
            )

            reranked_jobs.append(updated_job)

        # Sort by cross-encoder relevance.
        reranked_jobs.sort(
            key=lambda item: item["cross_encoder_score"],
            reverse=True
        )

        # Assign cross-encoder ranks.
        for position, job in enumerate(
            reranked_jobs,
            start=1
        ):
            job["cross_encoder_rank"] = position

        return reranked_jobs[:top_k]

    except Exception:
        logger.exception("Cross-encoder reranking failed")
        raise
