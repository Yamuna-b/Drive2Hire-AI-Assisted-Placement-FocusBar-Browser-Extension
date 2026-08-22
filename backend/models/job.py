from sqlalchemy import Column, Integer, String, Text, JSON
from backend.db.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    company_name = Column(String(255), nullable=False, index=True)
    location = Column(String(255), nullable=True)
    experience_range = Column(String(100), nullable=True)
    jd_text = Column(Text, nullable=True)
    mandatory_skills = Column(JSON, nullable=True)
    nice_to_have_skills = Column(JSON, nullable=True)
