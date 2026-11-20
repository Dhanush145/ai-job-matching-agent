
from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class CandidateProfile(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

    education: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)

    experience_years: float = Field(default=0, ge=0)

    preferred_roles: list[str] = Field(default_factory=list)
    preferred_locations: list[str] = Field(default_factory=list)
