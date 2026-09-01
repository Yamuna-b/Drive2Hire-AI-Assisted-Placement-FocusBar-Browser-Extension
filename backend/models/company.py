from sqlalchemy import Column, Integer, String, JSON, DateTime
from datetime import datetime
from backend.db.database import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    type = Column(String(100), nullable=True)
    industry = Column(String(255), nullable=True)
    company_size = Column(String(50), nullable=True)  # Startup, SMB, Enterprise
    
    locations = Column(JSON, nullable=True)
    typical_roles = Column(JSON, nullable=True)  # Aggregated typical roles
    tech_stack = Column(JSON, nullable=True)
    
    # Salary bands (INR)
    salary_entry = Column(String(100), nullable=True)  # e.g., "₹6L - ₹14L"
    salary_mid = Column(String(100), nullable=True)  # e.g., "₹15L - ₹28L"
    salary_senior = Column(String(100), nullable=True)  # e.g., "₹30L - ₹50L+"
    
    salary_bands = Column(JSON, nullable=True)
    leadership = Column(JSON, nullable=True)
    
    # Aggregation metadata
    jobs_analyzed = Column(Integer, default=0)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "industry": self.industry,
            "company_size": self.company_size,
            "locations": self.locations or [],
            "typical_roles": self.typical_roles or [],
            "tech_stack": self.tech_stack or [],
            "salary_entry": self.salary_entry,
            "salary_mid": self.salary_mid,
            "salary_senior": self.salary_senior,
            "jobs_analyzed": self.jobs_analyzed,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
        }
