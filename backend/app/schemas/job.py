
from typing import Optional

from pydantic import (
    BaseModel,
    Field,
    model_validator,
)


class JobCreate(BaseModel):
    job_id: str
    title: str
    company: str
    location: str
    description: str

    required_skills: list[str] = Field(default_factory=list)

    experience_required: float = Field(
        default=0,
        ge=0,
    )

    employment_type: str = "Full-time"

    # Salary in Lakhs Per Annum
    salary_min_lpa: Optional[float] = Field(
        default=None,
        ge=0,
    )

    salary_max_lpa: Optional[float] = Field(
        default=None,
        ge=0,
    )

    @model_validator(mode="after")
    def validate_salary_range(self):
        if (
            self.salary_min_lpa is not None
            and self.salary_max_lpa is not None
            and self.salary_max_lpa < self.salary_min_lpa
        ):
            raise ValueError(
                "Maximum salary cannot be less than minimum salary."
            )

        return self


class JobResponse(JobCreate):
    id: int

    model_config = {
        "from_attributes": True
    }
