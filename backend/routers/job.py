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
    for item, category in [(skill, "required") for skill in required] + [(skill, "preferred") for skill in preferred]:
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
            priority = "High" if category == "required" else "Low"
            action = f"Build evidence for {name} and add it to your profile or resume."
        elif level in {"weak", "beginner", "learning"} or len(evidence) == 1:
            status = "weak"
            priority = "Medium"
            action = f"Add a concrete project or coding example that demonstrates {name}."
        else:
            status = "matched"
            priority = "Low"
            action = f"Highlight your {name} evidence for this application."
        findings.append({"skill": name, "category": category, "status": status, "evidence": evidence, "priority": priority, "action": action})

    required_findings = [item for item in findings if item["category"] == "required"]
    required_score = (sum(item["status"] == "matched" for item in required_findings) / len(required_findings) * 100) if required_findings else 0
    all_score = (sum(item["status"] == "matched" for item in findings) / len(findings) * 100) if findings else 0
    readiness_score = round(required_score * 0.6 + all_score * 0.4) if findings else 0
    return {
        "score": readiness_score,
        "formula": "60% required-skill match + 40% overall evidence coverage",
        "findings": findings,
        "matched": [item for item in findings if item["status"] == "matched"],
        "missing_required": [item for item in findings if item["status"] == "missing" and item["category"] == "required"],
        "weak_evidence": [item for item in findings if item["status"] == "weak"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


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
    readiness = _build_readiness(
        parsed["mandatory_skills"],
        parsed["nice_to_have_skills"],
        user_skills,
        request.resume_text,
        request.coding_stats,
    )

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
        "readiness": readiness,
        "retrieved_at": readiness["generated_at"],
        "extraction": {
            "confidence": "review recommended" if not request.title or not request.company or not request.jd else "medium",
            "needs_review": True,
            "source": request.page_url or "current page",
        },
        "source": "live_page",
    }
