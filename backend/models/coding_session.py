from sqlalchemy import Column, Integer, String, ForeignKey, JSON, DateTime
from datetime import datetime
from backend.db.database import Base


class CodingSession(Base):
    __tablename__ = "coding_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Session metadata
    platform = Column(String(50), nullable=False)  # leetcode, gfg, codeforces
    session_type = Column(String(50), nullable=True)  # practice, contest, interview_prep
    
    # Timing
    start_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    session_date = Column(DateTime, default=datetime.utcnow, index=True)
    duration_minutes = Column(Integer, nullable=True)
    
    # Problem solving data
    problem_id = Column(String(255), nullable=True)
    topics = Column(JSON, nullable=True)  # List of topics
    difficulty = Column(String(50), nullable=True)
    
    # Session statistics
    problems_count = Column(Integer, default=0)
    problems_solved = Column(Integer, default=0)
    
    # Detailed problems data
    problems_data = Column(JSON, nullable=True)  # Array of problems: {id, name, topic, difficulty, status, time, url}
    
    # Notes
    notes = Column(String(500), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "platform": self.platform,
            "session_type": self.session_type,
            "session_date": self.session_date.isoformat() if self.session_date else None,
            "duration_minutes": self.duration_minutes,
            "problems_count": self.problems_count,
            "problems_solved": self.problems_solved,
            "accuracy": round((self.problems_solved / self.problems_count * 100), 1) if self.problems_count > 0 else 0,
            "topics": self.topics or [],
            "difficulty": self.difficulty,
            "notes": self.notes
        }
