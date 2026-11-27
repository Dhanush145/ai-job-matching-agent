
from typing import Optional

from pydantic import (
    BaseModel,
    Field,
    model_validator,
)


INVALID_PLACEHOLDERS = {
    "string",
    "none",
    "null",
    "n/a",
    "unknown",
    "undefined",
}


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
    def validate_job_data(self):

        # Validate required text fields
        required_fields = {
            "job_id": self.job_id,
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "description": self.description,
        }

        for field_name, value in required_fields.items():
            if not value.strip():
                raise ValueError(
                    f"{field_name} cannot be empty."
                )

            if value.strip().lower() in INVALID_PLACEHOLDERS:
                raise ValueError(
                    f"{field_name} cannot contain placeholder values."
                )

        # Validate required skills
        for skill in self.required_skills:
            if not skill.strip():
                raise ValueError(
                    "Required skills cannot contain empty values."
                )

            if skill.strip().lower() in INVALID_PLACEHOLDERS:
                raise ValueError(
                    f"Invalid placeholder skill: {skill}"
                )

        # Validate salary range
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
