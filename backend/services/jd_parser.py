import json
import re
from pathlib import Path

EMPTY_SKILL_VALUES = {"", "na", "n/a", "n.a.", "none", "nil", "-", "--", "not applicable"}

LABELED_MANDATORY = re.compile(
    r"(?im)^\s*(?:must\s*have(?:\s+skills?)?|required(?:\s+skills?)?|mandatory(?:\s+skills?)?|"
    r"key\s+skills?|minimum\s+qualifications?)\s*[:\-]\s*(.+)$"
)
LABELED_NICE = re.compile(
    r"(?im)^\s*(?:good\s+to\s+have(?:\s+skills?)?|nice\s+to\s+have(?:\s+skills?)?|"
    r"preferred(?:\s+skills?)?|optional(?:\s+skills?)?)\s*[:\-]\s*(.+)$"
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
    r"^save$|^apply$|clicked apply|people clicked|reposted|messages|notifications|"
    r"account executive|client executive|business systems analyst"
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
    if p.lower() in {"applications", "actively", "bengaluru", "bangalore", "corporation", "india"}:
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
    raw = _normalize_whitespace(raw)
    if raw.lower() in EMPTY_SKILL_VALUES:
        return []
    parts = re.split(r"[,;/|]|\\band\\b", raw, flags=re.I)
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
            if term in SHORT_ALIAS_SKIP or len(term) < 4:
                if term not in {"java", "sql", "git", "aws", "css", "php", "gcp", "c++", "c#", ".net"}:
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
        name = known or phrase
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
    return {
        "minimum_years": int(years) if years else None,
        "focus_skill": skill_focus,
        "education": edu,
        "employment_type": (EMPLOYMENT_LINE.search(jd_text or "").group(1) if EMPLOYMENT_LINE.search(jd_text or "") else None),
    }


def parse_jd(jd_text: str) -> dict:
    """Extract mandatory / nice-to-have skills from the actual JD text."""
    skills_config = _load_skills_config()
    text = jd_text or ""
    mandatory_objs, nice_objs = _labeled_skills(text, skills_config)

    labeled_names = {s["name"].lower() for s in mandatory_objs + nice_objs}

    # Extra known skills from the rest of the JD (never invent stacks like Spring Boot).
    body_skills = _find_skills_in_text(text, skills_config)
    for name in body_skills:
        if name.lower() in labeled_names:
            continue
        if name.lower() in GENERIC_UNLESS_LABELED:
            continue
        if any(s["name"].lower() == name.lower() for s in mandatory_objs + nice_objs):
            continue
        if not mandatory_objs:
            mandatory_objs.append({"name": name, "duration": None, "source": "body"})
        else:
            if name not in [s["name"] for s in nice_objs]:
                nice_objs.append({"name": name, "duration": None, "source": "body"})

    experience = _extract_experience(text)
    if experience.get("minimum_years") and mandatory_objs:
        focus = (experience.get("focus_skill") or "").lower()
        for item in mandatory_objs:
            if not focus or item["name"].lower() in focus or focus in item["name"].lower():
                item["duration"] = f"{experience['minimum_years']}+ years"

    return {
        "mandatory_skills": mandatory_objs,
        "nice_to_have_skills": nice_objs,
        "experience": experience,
        "source": "page_text",
    }
