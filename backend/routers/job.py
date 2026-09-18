from datetime import datetime, timezone

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
    resume_text: str = ""
    coding_stats: dict = Field(default_factory=dict)


def _skill_name(item):
    return item.get("name", "") if isinstance(item, dict) else str(item)


def _coding_evidence(skill_name: str, coding_stats: dict) -> list[str]:
    evidence = []
    needle = skill_name.lower()
    for platform, stats in (coding_stats or {}).items():
        if not isinstance(stats, dict) or not stats.get("ok"):
            continue
        topics = stats.get("topics") or stats.get("topic_stats") or {}
        if isinstance(topics, dict) and any(needle in str(topic).lower() or str(topic).lower() in needle for topic in topics):
            evidence.append(f"{platform} topic activity")
    return evidence


def _build_readiness(required, preferred, user_skills, resume_text, coding_stats):
    profile = {_skill_name(skill).lower(): skill for skill in user_skills if _skill_name(skill)}
    resume_lower = (resume_text or "").lower()
    findings = []
    
    all_jd_items = [(skill, "required") for skill in required] + [(skill, "preferred") for skill in preferred]
    
    for item, category in all_jd_items:
        name = _skill_name(item)
        key = name.lower()
        evidence = []
        if key in profile:
            evidence.append("manually added profile skill")
        if key and key in resume_lower:
            evidence.append("resume")
        evidence.extend(_coding_evidence(name, coding_stats))
        level = (profile.get(key, {}).get("level") or "moderate").lower()
        
        if not evidence:
            status = "missing"
            priority = "High" if category == "required" else "Medium"
            action = f"Learn {name} basics — required in current JD."
        elif level in {"weak", "beginner", "learning"} or len(evidence) == 1:
            status = "weak"
            priority = "Medium"
            action = f"Add concrete project or coding proof for {name}."
        else:
            status = "matched"
            priority = "Low"
            action = f"Highlight your {name} experience for this role."
            
        findings.append({"skill": name, "category": category, "status": status, "evidence": evidence, "priority": priority, "action": action})

    matched_count = sum(1 for item in findings if item["status"] == "matched")
    weak_count = sum(1 for item in findings if item["status"] == "weak")
    total_count = max(1, len(findings))

    # Balanced score: matched = 1.0, weak = 0.5
    raw_score = ((matched_count * 1.0 + weak_count * 0.5) / total_count) * 100
    readiness_score = max(15, min(95, round(raw_score)))

    # Generate dynamic priority actions based on ACTUAL missing skills in this JD
    missing_skills = [f["skill"] for f in findings if f["status"] == "missing"]
    priority_actions = []
    if missing_skills:
        priority_actions.append({"priority": "High", "text": f"Learn {missing_skills[0]} basics (Required in current JD; absent from profile).", "time": "3 days"})
        if len(missing_skills) > 1:
            priority_actions.append({"priority": "High", "text": f"Build a hands-on project with {missing_skills[1]} (Required in current JD).", "time": "4 days"})
        if len(missing_skills) > 2:
            priority_actions.append({"priority": "Medium", "text": f"Explore {missing_skills[2]} fundamentals & query tuning.", "time": "2 days"})
    else:
        priority_actions.append({"priority": "Low", "text": "Profile matches all key JD requirements. Review system design & resume tips.", "time": "1 day"})

    return {
        "score": readiness_score,
        "formula": f"Based on {matched_count} matched skills and {weak_count} weak evidence skills out of {total_count} JD requirements.",
        "findings": findings,
        "matched": [item for item in findings if item["status"] == "matched"],
        "missing_required": [item for item in findings if item["status"] == "missing" and item["category"] == "required"],
        "weak_evidence": [item for item in findings if item["status"] == "weak"],
        "priority_actions": priority_actions,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }



import re

@router.post("/analyse")
async def analyse_job(request: JobAnalyseRequest):
    jd_text = request.jd or ""
    page_url = request.page_url or ""
    
    company_name = (request.company or "").strip()
    if not company_name or company_name.lower() in ("unknown company", "could not read company"):
        if "linkedin.com" in page_url.lower() or "linkedin is the world" in jd_text.lower():
            company_name = "LinkedIn"
        elif "tcs" in jd_text.lower()[:300]:
            company_name = "TCS"
        elif "mailercloud" in jd_text.lower()[:300]:
            company_name = "MailerCloud"

    job_title = (request.title or "").strip()
    if not job_title:
        first_line = jd_text.splitlines()[0] if jd_text else ""
        if len(first_line) > 3 and len(first_line) < 60 and not re.search(r"http|www", first_line):
            job_title = first_line.strip()
        else:
            job_title = "Technical Systems Engineer"

    parsed = parse_jd(jd_text)
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
    readiness = _build_readiness(
        parsed["mandatory_skills"],
        parsed["nice_to_have_skills"],
        user_skills,
        request.resume_text,
        request.coding_stats,
    )

    return {
        "title": job_title,
        "company": company_name or "Target Enterprise",
        "location": request.location or "Bengaluru, Karnataka, India",
        "work_mode": request.work_mode or "Hybrid",
        "page_url": page_url,
        "jd_excerpt": jd_text[:400],
        "mandatory_skills": parsed["mandatory_skills"],
        "nice_to_have_skills": parsed["nice_to_have_skills"],
        "experience": parsed.get("experience") or {},
        "match": match,
        "match_percent": match_pct,
        "readiness": readiness,
        "retrieved_at": readiness["generated_at"],
        "extraction": {
            "confidence": "review recommended" if not request.title or not request.company or not request.jd else "medium",
            "needs_review": True,
            "source": request.page_url or "current page",
        },
        "source": "live_page",
    }
