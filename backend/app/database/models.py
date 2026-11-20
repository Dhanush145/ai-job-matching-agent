
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float
)

from .database import Base


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(150))
    email = Column(String(150), index=True)

    phone = Column(String(30))

    education = Column(Text)

    skills = Column(Text)

    experience_years = Column(Float, default=0)

    preferred_roles = Column(Text)

    preferred_locations = Column(Text)

    resume_filename = Column(String(255))


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)

    job_id = Column(String(50), unique=True, index=True)

    title = Column(String(150))
    company = Column(String(150))

    location = Column(String(150))

    description = Column(Text)

    required_skills = Column(Text)

    experience_required = Column(Float, default=0)

    employment_type = Column(String(50))
