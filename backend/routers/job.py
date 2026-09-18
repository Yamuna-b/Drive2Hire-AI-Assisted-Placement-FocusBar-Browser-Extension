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
    
    skill_action_map = {
        "Go": ("High", "Learn Go basics and concurrency (Required in JD; absent from profile).", "5 days"),
        "PHP": ("High", "Practice PHP 8 API development and object-oriented patterns.", "4 days"),
        "Vue 3": ("High", "Build a hands-on Vue 3 project (Frontend requirement in JD).", "5 days"),
        "MySQL": ("High", "Practice MySQL schema design, indexing, and query optimization.", "4 days"),
        "ClickHouse": ("Medium", "Learn ClickHouse basics for high-performance analytics.", "3 days"),
        "RabbitMQ": ("Medium", "Explore RabbitMQ message queues and event infrastructure.", "3 days"),
        "macOS": ("High", "Learn macOS endpoint administration and shell scripting.", "3 days"),
        "Windows": ("High", "Review Windows enterprise endpoint support & management.", "3 days"),
        "Office 365": ("Medium", "Master Office 365 administration (Exchange, Teams, SharePoint).", "3 days"),
        "Azure": ("Medium", "Learn Azure cloud infrastructure & integration basics.", "4 days"),
        "ServiceNow": ("Medium", "Explore ServiceNow ITSM incident & change workflows.", "2 days"),
    }

    for skill in missing_skills[:5]:
        if skill in skill_action_map:
            prio, text, tm = skill_action_map[skill]
            priority_actions.append({"priority": prio, "text": text, "time": tm})
        else:
            prio = "High" if len(priority_actions) < 2 else "Medium"
            priority_actions.append({"priority": prio, "text": f"Learn {skill} fundamentals for this position.", "time": "3 days"})

    if not priority_actions:
        priority_actions.append({"priority": "Low", "text": "Profile matches all key JD requirements. Review system design & interview prep.", "time": "1 day"})

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
    if company_name.lower() in ("unknown company", "could not read company"):
        company_name = ""

    job_title = (request.title or "").strip()
    if not job_title:
        first_line = jd_text.splitlines()[0] if jd_text else ""
        if len(first_line) > 3 and len(first_line) < 60 and not re.search(r"http|www", first_line):
            job_title = first_line.strip()

    loc = (request.location or "").strip()
    if loc.lower() in ("unknown", "location not stated"):
        loc = ""
    if not loc:
        if re.search(r"kozhikode|calicut", jd_text, re.I):
            loc = "Kozhikode, Kerala, India"
        elif re.search(r"bengaluru|bangalore", jd_text, re.I):
            loc = "Bengaluru, Karnataka, India"
        elif re.search(r"hyderabad", jd_text, re.I):
            loc = "Hyderabad, Telangana, India"
        elif re.search(r"pune", jd_text, re.I):
            loc = "Pune, Maharashtra, India"
        elif re.search(r"chennai", jd_text, re.I):
            loc = "Chennai, Tamil Nadu, India"
        elif re.search(r"remote|work from home", jd_text, re.I):
            loc = "Remote"

    work_mode = (request.work_mode or "").strip()
    if not work_mode:
        mode_match = re.search(r"\b(On-site|Hybrid|Remote|Work from home)\b", jd_text, re.I)
        if mode_match:
            work_mode = mode_match.group(1)

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
        "company": company_name,
        "location": loc,
        "work_mode": work_mode,
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
