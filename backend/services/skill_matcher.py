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

    mandatory_skills and nice_to_have_skills are lists of dicts {"name": str, "duration": str|None}.
    user_skills items: { "name": str, "level": str, "duration_bucket": str|None, "project_notes": str|None }
    """
    # Build lookup of user skills by normalized name
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

    # Helper to extract name from possible dict or string
    def _name(item):
        return item["name"] if isinstance(item, dict) else item

    # Aggregate unique skill names from JD
    all_skills = []
    seen = set()
    for skill in mandatory_skills + nice_to_have_skills:
        name = _name(skill)
        if name not in seen:
            all_skills.append(name)
            seen.add(name)

    result = {"covered": [], "weak": [], "missing": [], "needs_duration": []}
    for skill in all_skills:
        bucket = classify(skill)
        result[bucket].append(skill)

    # Detect duration gaps: JD skill has a duration requirement but user lacks duration_bucket
    for skill_item in mandatory_skills + nice_to_have_skills:
        if isinstance(skill_item, dict):
            name = skill_item.get("name")
            jd_duration = skill_item.get("duration")
            if jd_duration:
                user_entry = user_map.get(_normalize_skill_name(name))
                if not user_entry or not user_entry.get("duration_bucket"):
                    result["needs_duration"].append({"name": name, "required_duration": jd_duration})

    return result
