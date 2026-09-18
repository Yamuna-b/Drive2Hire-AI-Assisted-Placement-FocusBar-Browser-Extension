import json
import re
from pathlib import Path

EMPTY_SKILL_VALUES = {"", "na", "n/a", "n.a.", "none", "nil", "-", "--", "not applicable"}

LABELED_MANDATORY = re.compile(
    r"(?im)^\s*(?:must\s*have(?:\s+skills?)?|required(?:\s+skills?)?|mandatory(?:\s+skills?)?|"
    r"key\s+skills?|minimum\s+qualifications?|basic\s+qualifications?|qualifications?|requirements?)\s*[:\-]?\s*(.+)$"
)
LABELED_NICE = re.compile(
    r"(?im)^\s*(?:good\s+to\s+have(?:\s+skills?)?|nice\s+to\s+have(?:\s+skills?)?|"
    r"preferred(?:\s+skills?)?|optional(?:\s+skills?)?|suggested\s+skills?)\s*[:\-]?\s*(.+)$"
)
EXPERIENCE_LINE = re.compile(
    r"(?i)minimum\s+(\d+)\s*year\(s\)?\s+of\s+experience|"
    r"(\d+)\+?\s*years?\s+of\s+(?:proven\s+)?experience|"
    r"minimum\s+of\s+(\d+)\s+years?"
)
EDUCATION_LINE = re.compile(
    r"(?im)educational\s+qualification\s*[:\-]\s*(.+)$|"
    r"(\d+)\s+years?\s+(?:of\s+)?full\s+time\s+education"
)
EMPLOYMENT_LINE = re.compile(r"(?i)\b(full[- ]time|part[- ]time|contract|internship|temporary)\b")

JUNK_PHRASE = re.compile(
    r"(?i)easy apply|actively hiring|see more|show more|promoted|save job|"
    r"^save$|^apply$|clicked apply|people clicked|reposted|messages|notifications"
)

GENERIC_UNLESS_LABELED = {
    "accessibility",
    "frontend development",
    "backend development",
    "full stack development",
    "web development",
    "infrastructure",
    "data analytics",
    "data science",
    "machine learning",
    "performance",
    "monitoring",
    "logging",
    "networking",
    "compliance",
    "requirements analysis",
    "business analysis",
    "mobile development",
}

SHORT_ALIAS_SKIP = {"ai", "ml", "ui", "cv", "bi", "r"}
_SKILLS_CACHE = None


def _is_junk_phrase(phrase: str) -> bool:
    p = (phrase or "").strip()
    if len(p) < 2 or len(p) > 60:
        return True
    if JUNK_PHRASE.search(p):
        return True
    lower = p.lower()
    if lower in {"applications", "actively", "bengaluru", "bangalore", "corporation", "india", "b.s.", "b.a.", "qualifications", "qualifications:", "basic qualifications", "preferred qualifications", "requirements", "responsibilities"}:
        return True
    if re.search(r"\b(b\.?s\.?|b\.?a\.?|b\.?tech|m\.?tech|b\.?e\.?|m\.?s\.?)\b", lower):
        return True
    return False


def _load_skills_config():
    global _SKILLS_CACHE
    if _SKILLS_CACHE is not None:
        return _SKILLS_CACHE

    config_path = Path(__file__).resolve().parent.parent / "data" / "skills.json"
    with open(config_path, encoding="utf-8") as f:
        data = json.load(f)

    entries = []
    for item in data.get("skills", []):
        names = [item["name"]] + [a for a in item.get("aliases", []) if a.lower() != "spring"]
        terms = sorted({n.lower() for n in names if n}, key=len, reverse=True)
        entries.append({"canonical": item["name"], "terms": terms})

    entries.sort(key=lambda e: max((len(t) for t in e["terms"]), default=0), reverse=True)
    _SKILLS_CACHE = entries
    return entries


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _split_skill_list(raw: str) -> list:
    if not raw or raw.lower() in EMPTY_SKILL_VALUES:
        return []
    parts = re.split(r"[\n\r,;/|•*►▸\t]|\band\b", raw, flags=re.I)
    cleaned = []
    for part in parts:
        value = _normalize_whitespace(part)
        if value.lower() in EMPTY_SKILL_VALUES or len(value) < 2:
            continue
        cleaned.append(value)
    return cleaned


def _match_known_skill(phrase: str, skills_config: list) -> str | None:
    lower = phrase.lower().strip()
    for entry in skills_config:
        for term in entry["terms"]:
            if lower == term or lower.replace(" ", "") == term.replace(" ", ""):
                return entry["canonical"]
            escaped = re.escape(term).replace(r"\ ", r"\s+")
            if re.search(r"\b" + escaped + r"\b", lower):
                return entry["canonical"]
    return None


def _find_skills_in_text(text: str, skills_config: list) -> list:
    if not text:
        return []
    lower_text = text.lower()
    found = []
    seen = set()
    for entry in skills_config:
        canonical = entry["canonical"]
        if canonical in seen:
            continue
        for term in entry["terms"]:
            if len(term) < 2 and term not in {"c", "r"}:
                continue
            escaped = re.escape(term).replace(r"\ ", r"\s+")
            if re.search(r"\b" + escaped + r"\b", lower_text):
                found.append(canonical)
                seen.add(canonical)
                break
    return found


def _labeled_skills(jd_text: str, skills_config: list) -> tuple[list, list]:
    mandatory = []
    nice = []
    seen_m, seen_n = set(), set()

    def add(bucket, seen, phrase):
        if _is_junk_phrase(phrase):
            return
        known = _match_known_skill(phrase, skills_config)
        if not known:
            return  # Only accept validated skills from skills database
        name = known
        key = name.lower()
        if key in seen:
            return
        seen.add(key)
        bucket.append({"name": name, "duration": None, "source": "labeled"})

    for match in LABELED_MANDATORY.finditer(jd_text or ""):
        for phrase in _split_skill_list(match.group(1)):
            add(mandatory, seen_m, phrase)
    for match in LABELED_NICE.finditer(jd_text or ""):
        for phrase in _split_skill_list(match.group(1)):
            add(nice, seen_n, phrase)
    return mandatory, nice



def _extract_experience(jd_text: str) -> dict:
    years = None
    skill_focus = None
    edu = None
    for match in EXPERIENCE_LINE.finditer(jd_text or ""):
        years = next((g for g in match.groups() if g), years)
    edu_match = EDUCATION_LINE.search(jd_text or "")
    if edu_match:
        edu = _normalize_whitespace(next((g for g in edu_match.groups() if g), "") or edu_match.group(0))
    focus = re.search(
        r"(?i)experience in ([A-Za-z0-9 .+\-]+?)(?:\.|$)",
        jd_text or "",
    )
    if focus:
        skill_focus = _normalize_whitespace(focus.group(1))
    
    # Extract Level and Relocation info strictly if present
    level = None
    if re.search(r"\bsenior|sr\b|lead|principal|l5|l6", jd_text or "", re.I):
        level = "Senior"
    elif re.search(r"\bintern|junior|jr|fresh|entry|l3", jd_text or "", re.I):
        level = "Entry Level"
    elif re.search(r"\bmid[- ]level|mid\b", jd_text or "", re.I):
        level = "Mid-Level"

    relocation = "Yes" if re.search(r"relocat|relocation", jd_text or "", re.I) else None
    emp_match = EMPLOYMENT_LINE.search(jd_text or "")
    employment_type = emp_match.group(1) if emp_match else None

    return {
        "minimum_years": int(years) if years else None,
        "focus_skill": skill_focus,
        "education": edu,
        "employment_type": employment_type,
        "level": level,
        "relocation": relocation,
    }


def _dedupe_skills_list(skill_objs: list) -> list:
    seen = set()
    deduped = []
    alias_map = {
        "vue": "Vue 3",
        "vuejs": "Vue 3",
        "vue.js": "Vue 3",
        "rest": "REST API",
        "restful": "REST API",
        "m365": "Office 365",
        "microsoft 365": "Office 365",
        "anthropic api": "AI Fluency",
    }
    for item in skill_objs:
        name = item.get("name", "")
        norm = alias_map.get(name.lower(), name)
        key = norm.lower()
        if key not in seen:
            seen.add(key)
            item["name"] = norm
            deduped.append(item)
    return deduped


def parse_jd(jd_text: str) -> dict:
    """Extract mandatory / nice-to-have skills from the actual JD text."""
    skills_config = _load_skills_config()
    text = jd_text or ""
    mandatory_objs, nice_objs = _labeled_skills(text, skills_config)

    labeled_names = {s["name"].lower() for s in mandatory_objs + nice_objs}

    # Extract all matching skills in body
    body_skills = _find_skills_in_text(text, skills_config)
    unlabeled = [s for s in body_skills if s.lower() not in labeled_names and s.lower() not in GENERIC_UNLESS_LABELED]

    if not mandatory_objs and unlabeled:
        # Take top 3-4 skills as mandatory
        mand_count = min(4, len(unlabeled))
        for name in unlabeled[:mand_count]:
            mandatory_objs.append({"name": name, "duration": None, "source": "body"})
        for name in unlabeled[mand_count:]:
            nice_objs.append({"name": name, "duration": None, "source": "body"})
    else:
        for name in unlabeled:
            if not any(s["name"].lower() == name.lower() for s in nice_objs):
                nice_objs.append({"name": name, "duration": None, "source": "body"})

    # If no skills could be extracted, return empty lists with warning as requested
    if not mandatory_objs and not nice_objs:
        experience = _extract_experience(text)
        return {
            "mandatory_skills": [],
            "nice_to_have_skills": [],
            "experience": experience,
            "source": "page_text",
            "warning": "No skills could be extracted from the job description."
        }

    experience = _extract_experience(text)
    if experience.get("minimum_years") and mandatory_objs:
        focus = (experience.get("focus_skill") or "").lower()
        for item in mandatory_objs:
            if not focus or item["name"].lower() in focus or focus in item["name"].lower():
                item["duration"] = f"{experience['minimum_years']}+ years"

    clean_mand = _dedupe_skills_list(mandatory_objs)
    clean_nice = _dedupe_skills_list([s for s in nice_objs if s["name"].lower() not in {m["name"].lower() for m in clean_mand}])

    return {
        "mandatory_skills": clean_mand,
        "nice_to_have_skills": clean_nice,
        "experience": experience,
        "source": "page_text",
    }

