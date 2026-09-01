from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from datetime import datetime

from backend.services.jd_parser import parse_jd
from backend.services.skill_matcher import match_skills
from backend.db.database import get_db
from backend.models.job_outcome import JobOutcome

router = APIRouter()


class UserSkillInput(BaseModel):
    name: str
    level: str = "moderate"
    duration_bucket: str | None = None


class JobAnalyseRequest(BaseModel):
    title: str = ""
    company: str = ""
    jd: str = ""
    user_skills: list[UserSkillInput] = Field(default_factory=list)
    user_id: int = 1  # Default user ID


@router.post("/analyse")
async def analyse_job(request: JobAnalyseRequest, db: Session = Depends(get_db)):
    parsed = parse_jd(request.jd)
    user_skills = [s.model_dump() for s in request.user_skills]
    match = match_skills(
        parsed["mandatory_skills"],
        parsed["nice_to_have_skills"],
        user_skills,
    )

    # Auto-create application entry
    try:
        # Check if application already exists for this job
        existing_app = db.query(JobApplication).filter(
            JobApplication.user_id == request.user_id,
            JobApplication.company == request.company,
            JobApplication.job_title == request.title
        ).first()

        if not existing_app:
            # Calculate match score
            total_skills = len(parsed["mandatory_skills"]) + len(parsed["nice_to_have_skills"])
            covered_skills = len(match.get("covered", []))
            match_score = int((covered_skills / total_skills * 100)) if total_skills > 0 else 0

            new_app = JobApplication(
                user_id=request.user_id,
                company=request.company,
                job_title=request.title,
                jd_url=None,  # Could be passed in request
                match_score=match_score,
                application_status="applied",
                application_date=datetime.utcnow(),
                notes="Auto-created from job analysis"
            )
            db.add(new_app)
            db.commit()
    except Exception as e:
        # Don't fail the analysis if application creation fails
        pass

    return {
        "title": request.title,
        "company": request.company,
        "mandatory_skills": parsed["mandatory_skills"],
        "nice_to_have_skills": parsed["nice_to_have_skills"],
        "match": match,
    }
