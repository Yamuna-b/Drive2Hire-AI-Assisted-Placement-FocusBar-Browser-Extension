from sqlalchemy import Column, Integer, String, ForeignKey, JSON, DateTime
from backend.db.database import Base


class CodingSession(Base):
    __tablename__ = "coding_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    platform = Column(String(50), nullable=False)
    problem_id = Column(String(255), nullable=True)
    topics = Column(JSON, nullable=True)
    difficulty = Column(String(50), nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
