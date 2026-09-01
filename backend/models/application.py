"""Model for tracking job applications and outcomes."""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.db.database import Base


class Application(Base):
    __tablename__ = "applications"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Job details
    company = Column(String(255), nullable=False, index=True)
    job_title = Column(String(255), nullable=False)
    jd_url = Column(String(500), nullable=True)
    
    # Application tracking
    status = Column(String(50), default="applied", index=True)  # applied, shortlisted, interviewed, rejected, offered
    application_date = Column(DateTime, default=datetime.utcnow, index=True)
    follow_up_date = Column(DateTime, nullable=True)
    interview_date = Column(DateTime, nullable=True)
    
    # Matching & scoring
    match_score = Column(Integer, nullable=True)  # 0-100
    extracted_jd = Column(JSON, nullable=True)  # Extracted JD fields
    required_skills = Column(JSON, nullable=True)  # List of required skills
    
    # User notes
    notes = Column(String(1000), nullable=True)
    
    # Metadata
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", backref="applications")
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "company": self.company,
            "job_title": self.job_title,
            "status": self.status,
            "application_date": self.application_date.isoformat() if self.application_date else None,
            "interview_date": self.interview_date.isoformat() if self.interview_date else None,
            "match_score": self.match_score,
            "notes": self.notes,
            "days_since_application": (datetime.utcnow() - self.application_date).days if self.application_date else None
        }
