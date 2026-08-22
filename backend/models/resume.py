from sqlalchemy import Column, Integer, String, ForeignKey, Text, JSON, DateTime
from sqlalchemy.sql import func
from backend.db.database import Base


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    raw_text = Column(Text, nullable=True)
    structured_sections = Column(JSON, nullable=True)
    ats_flags = Column(JSON, nullable=True)
    version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
