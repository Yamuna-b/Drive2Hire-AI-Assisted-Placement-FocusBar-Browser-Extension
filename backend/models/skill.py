from sqlalchemy import Column, Integer, String
from backend.db.database import Base


class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    category = Column(String(100), nullable=True)
