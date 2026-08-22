from sqlalchemy import Column, Integer, String, JSON
from backend.db.database import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    type = Column(String(100), nullable=True)
    industry = Column(String(255), nullable=True)
    locations = Column(JSON, nullable=True)
    roles = Column(JSON, nullable=True)
    tech_stack = Column(JSON, nullable=True)
    salary_bands = Column(JSON, nullable=True)
    leadership = Column(JSON, nullable=True)
