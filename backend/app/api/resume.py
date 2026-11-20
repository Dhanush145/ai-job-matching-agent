
import json

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database.models import Candidate
from app.services.resume_parser import extract_resume_text
from app.services.profile_extractor import extract_candidate_profile


router = APIRouter(prefix="/api/resume", tags=["Resume"])


@router.post("/upload")
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF resumes are supported."
        )

    file_bytes = await file.read()

    if len(file_bytes) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="Resume must be smaller than 5 MB."
        )

    if not file_bytes.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=400,
            detail="Invalid PDF file."
        )

    try:
        resume_text = extract_resume_text(file_bytes)

        if len(resume_text) > 30000:
            resume_text = resume_text[:30000]

        profile = extract_candidate_profile(resume_text)

        candidate = Candidate(
            name=profile.name,
            email=str(profile.email) if profile.email else None,
            phone=profile.phone,
            education=json.dumps(profile.education),
            skills=json.dumps(profile.skills),
            experience_years=profile.experience_years,
            preferred_roles=json.dumps(profile.preferred_roles),
            preferred_locations=json.dumps(profile.preferred_locations),
            resume_filename=file.filename
        )

        db.add(candidate)
        db.commit()
        db.refresh(candidate)

        return {
            "message": "Resume processed successfully",
            "candidate_id": candidate.id,
            "profile": profile.model_dump(mode="json")
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc)
        )

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Resume processing failed: {str(exc)}"
        )


@router.get("/profile/{candidate_id}")
def get_candidate_profile(
    candidate_id: int,
    db: Session = Depends(get_db)
):
    candidate = db.query(Candidate).filter(
        Candidate.id == candidate_id
    ).first()

    if not candidate:
        raise HTTPException(
            status_code=404,
            detail="Candidate not found."
        )

    return {
        "id": candidate.id,
        "name": candidate.name,
        "email": candidate.email,
        "phone": candidate.phone,
        "education": json.loads(candidate.education or "[]"),
        "skills": json.loads(candidate.skills or "[]"),
        "experience_years": candidate.experience_years,
        "preferred_roles": json.loads(
            candidate.preferred_roles or "[]"
        ),
        "preferred_locations": json.loads(
            candidate.preferred_locations or "[]"
        )
    }
