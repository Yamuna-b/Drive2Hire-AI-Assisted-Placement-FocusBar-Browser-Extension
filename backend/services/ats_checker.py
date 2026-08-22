"""
Rule-based ATS (Applicant Tracking System) checker.

Checks a resume text against a parsed job description and returns:
- An ATS score (0-100)
- Keywords present / missing
- Formatting flags (no tables detected, bullet point usage, length)
"""
import re
from backend.services.jd_parser import parse_jd, _load_skills_config, _find_skills_in_text


# ATS formatting red flags
_FORMATTING_RULES = [
    {
        "id": "no_contact",
        "check": lambda text: not bool(re.search(r"[\w.\-]+@[\w\-]+\.[a-z]{2,}", text, re.I)),
        "message": "No email address found — ATS may reject resume.",
        "severity": "error",
    },
    {
        "id": "too_short",
        "check": lambda text: len(text.split()) < 150,
        "message": "Resume seems very short (< 150 words) — add more detail.",
        "severity": "warning",
    },
    {
        "id": "too_long",
        "check": lambda text: len(text.split()) > 1200,
        "message": "Resume is very long (> 1200 words) — consider condensing.",
        "severity": "warning",
    },
    {
        "id": "no_bullets",
        "check": lambda text: not bool(re.search(r"^[\s]*[-•*►▸]", text, re.MULTILINE)),
        "message": "No bullet points detected — use bullet points for ATS readability.",
        "severity": "info",
    },
    {
        "id": "table_risk",
        "check": lambda text: bool(re.search(r"\|[\s\w]+\|", text)),
        "message": "Pipe characters detected — tables may not parse correctly in ATS.",
        "severity": "warning",
    },
    {
        "id": "no_sections",
        "check": lambda text: not bool(re.search(
            r"\b(experience|education|skills|projects|summary|objective|certifications)\b",
            text, re.I
        )),
        "message": "No standard section headings found (Experience, Education, Skills, Projects).",
        "severity": "error",
    },
]

# Action verbs that signal strong resume writing
_ACTION_VERBS = [
    "developed", "built", "designed", "implemented", "led", "managed", "improved",
    "increased", "reduced", "delivered", "created", "architected", "deployed",
    "optimized", "automated", "integrated", "analysed", "launched", "maintained",
    "collaborated", "contributed", "mentored", "scaled", "migrated",
]


def check_ats(resume_text: str, jd_text: str = "", mandatory_skills: list = None, nice_to_have_skills: list = None) -> dict:
    """
    Run ATS checks on a resume against an optional job description.

    Args:
        resume_text: raw resume text (plain text, copied from PDF/doc)
        jd_text: raw JD text (optional — used for keyword matching)
        mandatory_skills: pre-parsed mandatory skills list (dicts with 'name')
        nice_to_have_skills: pre-parsed nice-to-have skills list

    Returns dict with:
        score: int (0-100)
        keyword_matches: list of str (skills found in resume that match JD)
        keyword_missing: list of str (JD skills NOT found in resume)
        formatting_flags: list of {message, severity}
        action_verb_count: int
        word_count: int
        tips: list of str
    """
    if not resume_text or not resume_text.strip():
        return {
            "score": 0,
            "keyword_matches": [],
            "keyword_missing": [],
            "formatting_flags": [],
            "action_verb_count": 0,
            "word_count": 0,
            "tips": ["Paste your resume text first."],
        }

    text = resume_text.strip()
    lower_text = text.lower()

    # --- Formatting flags ---
    formatting_flags = []
    for rule in _FORMATTING_RULES:
        if rule["check"](text):
            formatting_flags.append({"message": rule["message"], "severity": rule["severity"]})

    # --- Action verb count ---
    action_verb_count = sum(1 for v in _ACTION_VERBS if re.search(r"\b" + v + r"\b", lower_text))

    # --- Keyword matching against JD ---
    skills_config = _load_skills_config()

    # Collect all JD skill names
    jd_skills = []
    seen = set()
    for item in (mandatory_skills or []) + (nice_to_have_skills or []):
        name = item["name"] if isinstance(item, dict) else item
        if name.lower() not in seen:
            jd_skills.append(name)
            seen.add(name.lower())

    # If no pre-parsed skills, parse the JD now
    if not jd_skills and jd_text:
        parsed = parse_jd(jd_text)
        for item in parsed["mandatory_skills"] + parsed["nice_to_have_skills"]:
            name = item["name"]
            if name.lower() not in seen:
                jd_skills.append(name)
                seen.add(name.lower())

    # Check which JD skills appear in resume
    resume_skills = set(_find_skills_in_text(lower_text, skills_config))
    keyword_matches = [s for s in jd_skills if s.lower() in {r.lower() for r in resume_skills}]
    keyword_missing = [s for s in jd_skills if s.lower() not in {r.lower() for r in resume_skills}]

    # --- Score calculation ---
    # Base: 50 points
    # Keyword coverage: up to 30 points
    # Formatting (penalty per error/warning): up to -20 points
    # Action verbs: up to 10 points
    # Length bonus: up to 10 points

    score = 50

    if jd_skills:
        coverage = len(keyword_matches) / len(jd_skills)
        score += round(coverage * 30)
    else:
        # No JD — give partial keyword credit based on resume richness
        score += min(15, len(resume_skills) * 2)

    # Deduct for formatting issues
    severity_penalty = {"error": 8, "warning": 4, "info": 1}
    for flag in formatting_flags:
        score -= severity_penalty.get(flag["severity"], 2)

    # Action verb bonus (up to 10)
    score += min(10, action_verb_count)

    # Word count bonus (optimal 300-700 words)
    wc = len(text.split())
    if 300 <= wc <= 700:
        score += 10
    elif 200 <= wc < 300 or 700 < wc <= 900:
        score += 5

    score = max(0, min(100, score))

    # --- Tips ---
    tips = []
    if keyword_missing:
        tips.append(f"Add these missing keywords from the JD: {', '.join(keyword_missing[:6])}{'...' if len(keyword_missing) > 6 else ''}.")
    if action_verb_count < 5:
        tips.append("Use stronger action verbs: Built, Designed, Improved, Led, Deployed, Automated.")
    if wc < 200:
        tips.append("Expand your resume — most ATS systems prefer 250–700 words.")
    if not any(f["id"] == "no_contact" for f in [r for r in _FORMATTING_RULES if r["check"](text)]):
        pass  # contact info present
    if score >= 80:
        tips.append("Great match! Your resume aligns well with this job.")
    elif score >= 60:
        tips.append("Good resume — adding missing keywords will push your score higher.")
    else:
        tips.append("Focus on tailoring your resume to match the JD keywords.")

    return {
        "score": score,
        "keyword_matches": keyword_matches,
        "keyword_missing": keyword_missing,
        "formatting_flags": formatting_flags,
        "action_verb_count": action_verb_count,
        "word_count": wc,
        "tips": tips,
    }
