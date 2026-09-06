from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

from backend.services.jd_parser import parse_jd

router = APIRouter()


class PageCompanyRequest(BaseModel):
    company_name: str = ""
    job_title: Optional[str] = None
    jd: str = ""
    location: str = ""
    page_url: str = ""


@router.post("/from-page")
async def company_from_page(request: PageCompanyRequest):
    """Company insights from the current page text only — no canned profiles."""
    parsed = parse_jd(request.jd or "")
    skills = [s["name"] for s in parsed["mandatory_skills"] + parsed["nice_to_have_skills"]]
    experience = parsed.get("experience") or {}

    locations = []
    if request.location:
        locations.append(request.location)

    return {
        "name": request.company_name or "Unknown company",
        "job_title": request.job_title or "",
        "locations": locations,
        "tech_stack": skills,
        "typical_roles": [request.job_title] if request.job_title else [],
        "experience": experience,
        "salary_bands": None,
        "leadership": None,
        "source": "this_page",
        "note": "Shown only from the open page. Salary/leadership need a confirmed data source later.",
        "page_url": request.page_url,
    }


@router.post("/analyze-realtime")
async def analyze_company_realtime(request: PageCompanyRequest):
    return await company_from_page(request)


@router.get("/test")
async def test():
    return {"msg": "company router works"}
