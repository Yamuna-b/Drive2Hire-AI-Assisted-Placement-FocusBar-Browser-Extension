import json
import re
from pathlib import Path

MANDATORY_HEADING_PATTERNS = [
    r"\b(required|must have|must-have|mandatory|minimum qualifications?|essential|key requirements?|qualifications?|requirements?|what you.ll need|what we.re looking for)\b",
]

NICE_TO_HAVE_HEADING_PATTERNS = [
    r"\b(nice to have|nice-to-have|preferred|bonus|good to have|optional|plus points?|desirable|would be a plus)\b",
]

_SKILLS_CACHE = None


def _load_skills_config():
    global _SKILLS_CACHE
    if _SKILLS_CACHE is not None:
        return _SKILLS_CACHE

    config_path = Path(__file__).resolve().parent.parent / "data" / "skills.json"
    with open(config_path, encoding="utf-8") as f:
        data = json.load(f)

    entries = []
    for item in data.get("skills", []):
        names = [item["name"]] + item.get("aliases", [])
        entries.append({"canonical": item["name"], "terms": [n.lower() for n in names]})

    _SKILLS_CACHE = entries
    return entries


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _split_jd_sections(jd_text: str) -> dict:
    """Split JD into mandatory, nice-to-have, and other sections using heading heuristics."""
    lines = jd_text.splitlines()
    sections = {"mandatory": [], "nice_to_have": [], "other": []}
    current = "other"

    heading_re = re.compile(
        r"^[\s\*\-•]*([A-Za-z0-9][A-Za-z0-9\s/&\-]{2,60})\s*:?\s*$"
    )

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        lower = stripped.lower()
        is_heading = bool(heading_re.match(stripped)) and len(stripped) < 80

        if is_heading:
            if any(re.search(p, lower) for p in MANDATORY_HEADING_PATTERNS):
                current = "mandatory"
                continue
            if any(re.search(p, lower) for p in NICE_TO_HAVE_HEADING_PATTERNS):
                current = "nice_to_have"
                continue

        sections[current].append(stripped)

    return {
        key: _normalize_whitespace("\n".join(value))
        for key, value in sections.items()
    }


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
            pattern = r"\b" + re.escape(term).replace(r"\ ", r"\s+") + r"\b"
            if re.search(pattern, lower_text):
                found.append(canonical)
                seen.add(canonical)
                break

    return found


def parse_jd(jd_text: str) -> dict:
    """Extract mandatory and nice-to-have skills from a job description."""
    skills_config = _load_skills_config()
    sections = _split_jd_sections(jd_text or "")

    mandatory = _find_skills_in_text(sections["mandatory"], skills_config)
    nice_to_have = _find_skills_in_text(sections["nice_to_have"], skills_config)

    # Skills mentioned outside labelled sections default to mandatory.
    fallback = _find_skills_in_text(sections["other"], skills_config)
    mandatory_set = set(mandatory)
    nice_set = set(nice_to_have)

    for skill in fallback:
        if skill not in mandatory_set and skill not in nice_set:
            mandatory.append(skill)
            mandatory_set.add(skill)

    # If no section headings matched, scan the full JD as mandatory.
    if not mandatory and not nice_to_have and jd_text:
        mandatory = _find_skills_in_text(jd_text, skills_config)

    return {
        "mandatory_skills": mandatory,
        "nice_to_have_skills": nice_to_have,
    }
