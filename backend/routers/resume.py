from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List

from backend.services.ats_checker import check_ats

router = APIRouter()


class SkillItem(BaseModel):
    name: str
    duration: Optional[str] = None


class ResumeCheckRequest(BaseModel):
    resume_text: str
    jd_text: Optional[str] = ""
    mandatory_skills: Optional[List[SkillItem]] = []
    nice_to_have_skills: Optional[List[SkillItem]] = []


@router.post("/resume/check")
async def check_resume(request: ResumeCheckRequest):
    """
    Run a rule-based ATS check on resume text against the current job description.
    Returns an ATS score, keyword gap analysis, formatting flags, and actionable tips.
    """
    result = check_ats(
        resume_text=request.resume_text,
        jd_text=request.jd_text or "",
        mandatory_skills=[s.model_dump() for s in (request.mandatory_skills or [])],
        nice_to_have_skills=[s.model_dump() for s in (request.nice_to_have_skills or [])],
    )
    return result
