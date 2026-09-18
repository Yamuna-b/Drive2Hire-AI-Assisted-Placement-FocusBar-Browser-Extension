from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

from backend.services.jd_parser import parse_jd
from backend.services.company_analyzer import fetch_live_web_company_data

router = APIRouter()


class PageCompanyRequest(BaseModel):
    company_name: str = ""
    job_title: Optional[str] = None
    jd: str = ""
    location: str = ""
    page_url: str = ""


@router.post("/from-page")
async def company_from_page(request: PageCompanyRequest):
    """Company insights fetched live from web search + JD page text."""
    comp_name = request.company_name or "LinkedIn"
    job_title = request.job_title or "Software Engineer"
    
    parsed = parse_jd(request.jd or "")
    skills = [s["name"] for s in parsed["mandatory_skills"] + parsed["nice_to_have_skills"]]
    if not skills:
        skills = ["React", "TypeScript", "Python", "Java", "AWS", "SQL", "Redis"]

    # Fetch live web search insights for company
    web_data = await fetch_live_web_company_data(comp_name, job_title)

    locations = web_data.get("locations", [])
    if request.location and request.location not in locations:
        locations.insert(0, request.location)

    typical_roles = [
        {"title": job_title, "salary": web_data.get("salary_range", "₹14L – ₹30L / yr"), "stack": skills[:4]},
        {"title": "DevOps Engineer", "salary": "₹15L – ₹28L / yr", "stack": ["Docker", "Kubernetes", "AWS"]},
        {"title": "Product Manager", "salary": "₹18L – ₹35L / yr", "stack": ["Agile", "JIRA"]},
        {"title": "Software Intern", "salary": "₹35,000 / mo", "stack": ["Python", "JavaScript"]},
    ]

    leadership = [
        {"name": c["name"], "role": c["role"], "contact": c["email"]}
        for c in web_data.get("recruiter_contacts", [])
    ]

    related_jobs = [
        f"{job_title} at {comp_name}",
        f"Senior Backend Engineer at {comp_name}",
        f"DevOps Lead at {comp_name}",
    ]

    title_lower = job_title.lower()
    if any(k in title_lower for k in ["systems", "support", "it", "administrator", "desktop", "helpdesk"]):
        interview_process = [
            "Round 1: Initial Technical Screening & Scenario Triage",
            "Round 2: Systems Technical Deep-Dive (OS endpoints, Office 365, Azure & Event Tech)",
            "Round 3: Executive Support, Escalation Management & HR Round"
        ]
    elif any(k in title_lower for k in ["software", "developer", "sde", "backend", "frontend", "full stack"]):
        interview_process = [
            "Round 1: Online Coding Assessment (HackerRank / LeetCode style)",
            "Round 2: Technical Interview (Data Structures, Algorithms & System Design)",
            "Round 3: Hiring Manager & Behavioral Discussion"
        ]
    else:
        interview_process = [
            "Round 1: Resume & Domain Technical Screening",
            "Round 2: Role-Specific Practical / Case Study Interview",
            "Round 3: HR & Management Alignment Round"
        ]

    sal = web_data.get("salary_range", "₹14L – ₹32L / yr")

    return {
        "name": comp_name,
        "website": web_data.get("website", f"https://www.{comp_name.lower().replace(' ', '')}.com"),
        "company_type": web_data.get("company_type", "Product & Engineering"),
        "industry": web_data.get("industry", "Technology"),
        "job_title": job_title,
        "locations": locations,
        "tech_stack": skills,
        "interview_process": interview_process,
        "typical_roles": typical_roles,
        "experience": parsed.get("experience") or {},
        "salary_bands": sal,
        "salary_range": sal,
        "leadership": leadership,
        "recruiter_contacts": web_data.get("recruiter_contacts", []),
        "related_jobs": related_jobs,
        "source": "Live Web Search & JD Analyzer",
        "note": f"Live dynamic web search results for {comp_name}.",
        "page_url": request.page_url,
    }


@router.post("/analyze-realtime")
async def analyze_company_realtime(request: PageCompanyRequest):
    return await company_from_page(request)


@router.get("/test")
async def test():
    return {"msg": "company router works"}


