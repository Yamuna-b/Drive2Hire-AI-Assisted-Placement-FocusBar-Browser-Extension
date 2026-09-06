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
    location: str = ""
    work_mode: str = ""
    page_url: str = ""
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

    mandatory_names = [s["name"] for s in parsed["mandatory_skills"]]
    nice_names = [s["name"] for s in parsed["nice_to_have_skills"]]
    total = len(set(mandatory_names + nice_names))
    covered = len(match.get("covered", []))
    match_pct = int((covered / total) * 100) if total else 0

    return {
        "title": request.title,
        "company": request.company,
        "location": request.location,
        "work_mode": request.work_mode,
        "page_url": request.page_url,
        "jd_excerpt": (request.jd or "")[:400],
        "mandatory_skills": parsed["mandatory_skills"],
        "nice_to_have_skills": parsed["nice_to_have_skills"],
        "experience": parsed.get("experience") or {},
        "match": match,
        "match_percent": match_pct,
        "source": "live_page",
    }
