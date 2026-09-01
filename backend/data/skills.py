"""Skills database loader - loads skills from skills.json"""

import json
import os
from pathlib import Path
from typing import List, Dict

# Get the directory where this file is located
DATA_DIR = Path(__file__).parent


def load_skills_database() -> List[Dict]:
    """Load skills from skills.json file.
    
    Returns:
        List of skill dictionaries with fields: name, category, level, etc.
    """
    
    skills_file = DATA_DIR / "skills.json"
    
    if not skills_file.exists():
        print(f"Warning: {skills_file} not found. Returning empty skills database.")
        return []
    
    try:
        with open(skills_file, "r", encoding="utf-8") as f:
            skills_data = json.load(f)
        
        # Handle both dict and list formats
        if isinstance(skills_data, dict):
            # If it's a dict with skills key, extract the list
            if "skills" in skills_data:
                return skills_data["skills"]
            # Otherwise treat all values as skills
            return list(skills_data.values())
        elif isinstance(skills_data, list):
            return skills_data
        
        return []
    
    except Exception as e:
        print(f"Error loading skills database: {e}")
        return []


def get_skill_by_name(name: str) -> Dict | None:
    """Get a specific skill by name.
    
    Args:
        name: Skill name (case-insensitive)
    
    Returns:
        Skill dictionary or None if not found
    """
    
    skills = load_skills_database()
    name_lower = name.lower()
    
    for skill in skills:
        if skill.get("name", "").lower() == name_lower:
            return skill
    
    return None


def get_skills_by_category(category: str) -> List[Dict]:
    """Get all skills in a category.
    
    Args:
        category: Skill category name (case-insensitive)
    
    Returns:
        List of skills in that category
    """
    
    skills = load_skills_database()
    category_lower = category.lower()
    
    return [
        skill for skill in skills
        if skill.get("category", "").lower() == category_lower
    ]


def get_skill_categories() -> List[str]:
    """Get all unique skill categories.
    
    Returns:
        List of category names
    """
    
    skills = load_skills_database()
    categories = set()
    
    for skill in skills:
        cat = skill.get("category", "Other")
        if cat:
            categories.add(cat)
    
    return sorted(list(categories))
