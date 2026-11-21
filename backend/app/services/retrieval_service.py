
import json
from pathlib import Path

import faiss
import numpy as np

from app.database.models import Job
from app.services.embedding_service import embedding_service


BASE_DIR = Path(__file__).resolve().parents[3]

VECTOR_DIR = BASE_DIR / "vector_store"

VECTOR_DIR.mkdir(parents=True, exist_ok=True)

INDEX_PATH = VECTOR_DIR / "jobs.index"
METADATA_PATH = VECTOR_DIR / "jobs_metadata.json"


def create_job_document(job: Job) -> str:
    """
    Convert a job record into searchable text.
    """

    skills = json.loads(job.required_skills or "[]")

    return f"""
    Job Title: {job.title}

    Company: {job.company}

    Location: {job.location}

    Description: {job.description}

    Required Skills: {", ".join(skills)}

    Experience Required: {job.experience_required} years

    Employment Type: {job.employment_type}
    """


def build_job_index(db):
    """
    Generate embeddings for all jobs and
    create a FAISS vector index.
    """

    jobs = db.query(Job).order_by(Job.id).all()

    if not jobs:
        raise ValueError("No jobs found in database.")

    documents = [
        create_job_document(job)
        for job in jobs
    ]

    embeddings = embedding_service.generate_embeddings(
        documents
    )

    dimension = embeddings.shape[1]

    # Inner product on normalized vectors = cosine similarity
    index = faiss.IndexFlatIP(dimension)

    index.add(np.ascontiguousarray(embeddings))

    metadata = [
        {
            "job_id": job.job_id,
            "title": job.title,
            "company": job.company,
            "location": job.location
        }
        for job in jobs
    ]

    faiss.write_index(index, str(INDEX_PATH))

    with open(METADATA_PATH, "w", encoding="utf-8") as file:
        json.dump(metadata, file, indent=4)

    return {
        "message": "FAISS index created successfully",
        "total_jobs": len(jobs),
        "embedding_dimension": dimension
    }


def search_similar_jobs(
    query: str,
    top_k: int = 10
):
    """
    Retrieve the most semantically relevant jobs.
    """

    if not INDEX_PATH.exists() or not METADATA_PATH.exists():
        raise ValueError(
            "FAISS index not found. Build the index first."
        )

    index = faiss.read_index(str(INDEX_PATH))

    with open(METADATA_PATH, "r", encoding="utf-8") as file:
        metadata = json.load(file)

    query_embedding = embedding_service.generate_embedding(
        query
    )

    query_vector = np.ascontiguousarray(
        query_embedding.reshape(1, -1)
    )

    k = min(top_k, index.ntotal)

    scores, indices = index.search(
        query_vector,
        k
    )

    results = []

    for score, idx in zip(scores[0], indices[0]):

        if idx < 0:
            continue

        results.append({
            "job_id": metadata[idx]["job_id"],
            "title": metadata[idx]["title"],
            "company": metadata[idx]["company"],
            "location": metadata[idx]["location"],
            "similarity_score": round(
                float(score) * 100, 2
            )
        })

    return results
