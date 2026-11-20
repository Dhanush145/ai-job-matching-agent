
from pydantic import BaseModel, Field


class JobCreate(BaseModel):
    job_id: str
    title: str
    company: str
    location: str
    description: str

    required_skills: list[str] = Field(default_factory=list)
    experience_required: float = Field(default=0, ge=0)

    employment_type: str = "Full-time"


class JobResponse(JobCreate):
    id: int

    model_config = {"from_attributes": True}
