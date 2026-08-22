from fastapi import APIRouter
from pydantic import BaseModel, Field

from backend.services.jd_parser import parse_jd
from backend.services.skill_matcher import match_skills

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


@router.post("/analyse")
async def analyse_job(request: JobAnalyseRequest):
    parsed = parse_jd(request.jd)
    user_skills = [s.model_dump() for s in request.user_skills]
    match = match_skills(
        parsed["mandatory_skills"],
        parsed["nice_to_have_skills"],
        user_skills,
    )

    return {
        "title": request.title,
        "company": request.company,
        "mandatory_skills": parsed["mandatory_skills"],
        "nice_to_have_skills": parsed["nice_to_have_skills"],
        "match": match,
    }
