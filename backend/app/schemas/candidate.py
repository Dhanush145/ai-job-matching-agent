
from pydantic import BaseModel, EmailStr, Field, model_validator
from typing import Optional


class EducationEntry(BaseModel):
    institution: Optional[str] = None
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    graduation_year: Optional[str] = None
    cgpa: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def normalize_education(cls, value):
        # Support older LLM output where education is a string
        if isinstance(value, str):
            return {"degree": value}

        return value


class CandidateProfile(BaseModel):

    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

    education: list[EducationEntry] = Field(
        default_factory=list
    )

    skills: list[str] = Field(
        default_factory=list
    )

    experience_years: float = Field(
        default=0,
        ge=0
    )

    preferred_roles: list[str] = Field(
        default_factory=list
    )

    preferred_locations: list[str] = Field(
        default_factory=list
    )
