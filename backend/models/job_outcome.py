from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime
from backend.db.database import Base


class JobOutcome(Base):
    __tablename__ = "job_outcomes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, index=True)
    status = Column(String(50), nullable=False)
    reason = Column(Text, nullable=True)
    applied_at = Column(DateTime(timezone=True), nullable=True)
