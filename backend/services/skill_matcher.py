WEAK_LEVELS = {"weak", "beginner", "learning"}
STRONG_LEVELS = {"strong", "moderate", "intermediate", "advanced", "expert"}


def _normalize_skill_name(name: str) -> str:
    return name.strip().lower()


def match_skills(
    mandatory_skills: list,
    nice_to_have_skills: list,
    user_skills: list,
) -> dict:
    """
    Compare JD skills against a user profile.

    user_skills items: { "name": str, "level": str, "duration_bucket": str|None }
    """
    user_map = {}
    for skill in user_skills:
        key = _normalize_skill_name(skill.get("name", ""))
        if key:
            user_map[key] = skill

    def classify(skill_name: str) -> str:
        key = _normalize_skill_name(skill_name)
        profile = user_map.get(key)
        if not profile:
            return "missing"

        level = (profile.get("level") or "moderate").lower()
        if level in WEAK_LEVELS:
            return "weak"
        if level in STRONG_LEVELS:
            return "covered"
        return "weak"

    all_skills = []
    seen = set()
    for skill in mandatory_skills + nice_to_have_skills:
        if skill not in seen:
            all_skills.append(skill)
            seen.add(skill)

    result = {"covered": [], "weak": [], "missing": []}
    for skill in all_skills:
        bucket = classify(skill)
        result[bucket].append(skill)

    return result
