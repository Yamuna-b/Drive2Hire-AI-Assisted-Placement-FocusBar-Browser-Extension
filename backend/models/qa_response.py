from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from backend.db.database import Base


class QAResponse(Base):
    __tablename__ = "qa_responses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user_skill_id = Column(Integer, ForeignKey("user_skills.id"), nullable=True, index=True)
    skill_name = Column(String(255), nullable=False)
    has_experience = Column(Boolean, nullable=False)
    duration_bucket = Column(String(50), nullable=True)  # "<1 year", "1-2 years", "2+ years"
    project_notes = Column(Text, nullable=True)
    job_title = Column(String(255), nullable=True)
    job_company = Column(String(255), nullable=True)
    answered_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", backref="qa_responses")
    user_skill = relationship("UserSkill", backref="qa_responses")

    def to_dict(self):
        return {
            "id": self.id,
            "skill_name": self.skill_name,
            "has_experience": self.has_experience,
            "duration_bucket": self.duration_bucket,
            "project_notes": self.project_notes,
            "answered_at": self.answered_at.isoformat() if self.answered_at else None,
        }
