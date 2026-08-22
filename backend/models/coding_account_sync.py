from sqlalchemy import Column, Integer, String, ForeignKey, JSON, DateTime
from backend.db.database import Base


class CodingAccountSync(Base):
    __tablename__ = "coding_account_syncs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    platform = Column(String(50), nullable=False)
    handle = Column(String(255), nullable=False)
    total_solved = Column(Integer, default=0, nullable=False)
    topic_breakdown = Column(JSON, nullable=True)
    last_synced_at = Column(DateTime(timezone=True), nullable=True)
