from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.db.database import Base


class UserSkill(Base):
    __tablename__ = "user_skills"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False, index=True)
    duration_bucket = Column(String(50), nullable=True)
    project_notes = Column(Text, nullable=True)

    user = relationship("User", backref="user_skills")
    skill = relationship("Skill", backref="user_skills")
