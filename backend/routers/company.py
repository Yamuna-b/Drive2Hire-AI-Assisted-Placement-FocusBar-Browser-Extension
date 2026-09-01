from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import re
from backend.db.database import get_db
from backend.models.company import Company
from backend.services.company_analyzer import (
    extract_company_info,
    extract_roles_from_jd,
    extract_tech_from_jd,
    extract_salary_from_jd,
    get_or_create_company
)

router = APIRouter()


class CompanyAnalysisRequest(BaseModel):
    """Request company analysis from job posting."""
    title: str
    company: str
    jd: str


class CompanyInsightsResponse(BaseModel):
    """Company insights from aggregated data."""
    name: str
    locations: List[str]
    tech_stack: List[str]
    typical_roles: List[str]
    salary_entry: Optional[str]
    salary_mid: Optional[str]
    salary_senior: Optional[str]
    industry: Optional[str]
    company_size: Optional[str]
    jobs_analyzed: int


@router.post("/analyse")
async def analyze_company(request: CompanyAnalysisRequest, db: Session = Depends(get_db)):
    """Extract company information from a job posting."""
    
    company_name = request.company.strip()
    if not company_name:
        return {"error": "Company name required"}
    
    # Extract company info from job data
    company_info = extract_company_info({
        "company": company_name,
        "jd": request.jd,
        "title": request.title
    })
    
    # Get or create company in database
    company = get_or_create_company(db, company_name)
    
    # Update company with extracted data
    if company_info.get("tech_stack"):
        current_tech = set(company.tech_stack or [])
        current_tech.update(company_info["tech_stack"])
        company.tech_stack = list(current_tech)
    
    if company_info.get("roles"):
        current_roles = set(company.typical_roles or [])
        current_roles.update(company_info["roles"])
        company.typical_roles = list(current_roles)
    
    if company_info.get("salary"):
        company.salary_entry = company.salary_entry or company_info["salary"]
    
    company.jobs_analyzed = (company.jobs_analyzed or 0) + 1
    
    db.commit()
    
    return {
        "company": company_name,
        "extracted_roles": company_info.get("roles", []),
        "extracted_tech": company_info.get("tech_stack", []),
        "salary": company_info.get("salary"),
        "job_title": request.title
    }


@router.get("/profile/{company_name}")
async def get_company_profile(company_name: str, db: Session = Depends(get_db)):
    """Get complete company profile with insights."""
    
    company = db.query(Company).filter(
        Company.name.ilike(f"%{company_name}%")
    ).first()
    
    if not company:
        return {"error": f"No data found for {company_name}"}
    
    return {
        "name": company.name,
        "locations": company.locations or [],
        "tech_stack": company.tech_stack or [],
        "typical_roles": company.typical_roles or [],
        "salary_entry": company.salary_entry,
        "salary_mid": company.salary_mid,
        "salary_senior": company.salary_senior,
        "industry": company.industry,
        "company_size": company.company_size,
        "jobs_analyzed": company.jobs_analyzed or 0,
        "last_updated": company.last_updated
    }


@router.get("/search")
async def search_companies(q: str, db: Session = Depends(get_db)):
    """Search companies by name (for autocompletion)."""
    
    if not q or len(q) < 2:
        return {"companies": []}
    
    companies = db.query(Company).filter(
        Company.name.ilike(f"%{q}%")
    ).limit(10).all()
    
    return {
        "query": q,
        "companies": [
            {"name": c.name, "industry": c.industry}
            for c in companies
        ]
    }


@router.get("/{company_name}/roles")
async def get_company_roles(company_name: str, db: Session = Depends(get_db)):
    """Get typical roles and career paths at a company."""
    
    company = db.query(Company).filter(
        Company.name.ilike(f"%{company_name}%")
    ).first()
    
    if not company:
        return {"error": f"No data for {company_name}"}
    
    # Map roles to typical career progression
    role_progression = {
        "Software Engineer": ["Junior SDE", "SDE II", "SDE III", "Senior SDE"],
        "Frontend Developer": ["Junior Frontend", "Frontend Engineer", "Senior Frontend"],
        "Backend Developer": ["Junior Backend", "Backend Engineer", "Senior Backend"],
        "DevOps Engineer": ["Junior DevOps", "DevOps Engineer", "Senior DevOps"],
        "Data Engineer": ["Junior Data Engineer", "Data Engineer", "Senior Data Engineer"],
        "Product Manager": ["Associate PM", "Product Manager", "Senior PM", "Director"],
        "QA Engineer": ["QA Intern", "QA Engineer", "Senior QA", "QA Lead"],
    }
    
    return {
        "company": company_name,
        "typical_roles": company.typical_roles or [],
        "career_paths": role_progression,
        "growth_opportunities": "High" if company.company_size in ["Startup", "SMB"] else "Medium" if company.company_size == "Enterprise" else "Unknown"
    }


@router.get("/{company_name}/tech-stack")
async def get_company_tech_stack(company_name: str, db: Session = Depends(get_db)):
    """Get technology stack and skill requirements per role."""
    
    company = db.query(Company).filter(
        Company.name.ilike(f"%{company_name}%")
    ).first()
    
    if not company:
        return {"error": f"No data for {company_name}"}
    
    # Map typical tech stacks by role
    tech_by_role = {
        "Backend": ["Java", "Python", "Go", "SQL", "Microservices", "Docker", "AWS"],
        "Frontend": ["React", "JavaScript", "TypeScript", "CSS", "HTML", "Redux"],
        "DevOps": ["Docker", "Kubernetes", "Terraform", "Jenkins", "AWS", "Linux"],
        "Data": ["Python", "Spark", "SQL", "Hadoop", "Kafka"],
        "Mobile": ["React Native", "Flutter", "Swift", "Kotlin"],
    }
    
    tech_stack = company.tech_stack or []
    
    return {
        "company": company_name,
        "tech_stack": tech_stack,
        "tech_by_role": tech_by_role,
        "key_skills": list(set([t for tech_list in tech_by_role.values() for t in tech_list if t in tech_stack]))
    }


@router.get("/{company_name}/salary")
async def get_company_salary_ranges(company_name: str, db: Session = Depends(get_db)):
    """Get salary band estimates by level."""
    
    company = db.query(Company).filter(
        Company.name.ilike(f"%{company_name}%")
    ).first()
    
    if not company:
        return {"error": f"No salary data for {company_name}"}
    
    return {
        "company": company_name,
        "currency": "INR",
        "salary_bands": {
            "entry_level": company.salary_entry or "₹6L - ₹14L",
            "mid_level": company.salary_mid or "₹15L - ₹28L",
            "senior": company.salary_senior or "₹30L - ₹50L+",
        },
        "note": "Estimates based on available job postings"
    }


@router.get("/test")
async def test():
    return {"msg": "company router works"}
