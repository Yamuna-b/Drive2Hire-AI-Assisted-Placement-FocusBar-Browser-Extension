from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List

router = APIRouter()


class SkillQuestion(BaseModel):
    """Question about a skill with duration requirement."""
    skill_name: str
    required_duration: str
    questions: List[str] = Field(default_factory=list)


class UserSkillResponse(BaseModel):
    """User's response to skill experience questions."""
    skill_name: str
    has_experience: bool
    duration_bucket: str | None = None  # "<1 year", "1-2 years", "2+ years"
    project_notes: str | None = None


class QASessionRequest(BaseModel):
    """Request Q&A session for gap skills."""
    mandatory_skills: List[dict]
    nice_to_have_skills: List[dict]
    user_skills: List[dict]


def generate_qa_questions(skill_name: str, required_duration: str) -> List[str]:
    """Generate context-aware Q&A questions for a skill."""
    questions = [
        f"Do you have practical experience with {skill_name}?",
        f"Have you worked on any projects using {skill_name}?",
        f"Can you describe your {skill_name} experience in terms of duration?",
    ]
    
    # Add duration-specific questions
    if "2+" in required_duration or "3+" in required_duration:
        questions.append(
            f"The role requires {required_duration} of {skill_name} experience. "
            f"Can you share your hands-on project experience with {skill_name}?"
        )
    
    return questions


@router.get("/health")
async def qa_health():
    return {"msg": "Q&A router — Phase 3 endpoint"}


@router.post("/generate-questions")
async def generate_qa_session(request: QASessionRequest):
    """Generate Q&A questions for skills that need duration validation.
    
    Returns questions for mandatory skills that have duration requirements
    but the user's experience doesn't match.
    """
    
    # Build a map of user skills for quick lookup
    user_skill_map = {
        skill['name'].lower(): skill 
        for skill in request.user_skills
    }
    
    gap_skills = []
    
    # Check mandatory skills for gaps
    for skill_obj in request.mandatory_skills:
        skill_name = skill_obj.get('name', '')
        required_duration = skill_obj.get('duration')
        
        if not required_duration or not skill_name:
            continue
        
        user_skill = user_skill_map.get(skill_name.lower())
        
        # Gap exists if:
        # 1. User doesn't have the skill, OR
        # 2. User has it but duration doesn't match requirement
        has_gap = False
        
        if not user_skill:
            has_gap = True
        elif user_skill.get('duration_bucket'):
            # Compare duration buckets
            required = required_duration.lower()
            user_duration = user_skill['duration_bucket'].lower()
            
            # Simple comparison: if required is "2+ years" and user has less, it's a gap
            if "2+" in required or "3+" in required:
                if "1 year" in user_duration or "<1" in user_duration:
                    has_gap = True
        else:
            has_gap = True
        
        if has_gap:
            questions = generate_qa_questions(skill_name, required_duration or "")
            gap_skills.append({
                "name": skill_name,
                "required_duration": required_duration,
                "questions": questions
            })
    
    return {
        "session_id": None,  # Will be stored in frontend storage
        "gap_skills": gap_skills[:5],  # Limit to top 5 gaps for UX
        "total_gaps": len(gap_skills)
    }


@router.post("/save-responses")
async def save_qa_responses(responses: List[UserSkillResponse]):
    """Save user's Q&A responses for future reference.
    
    In Phase 4+, these can be persisted to database.
    For now, they're handled client-side via chrome.storage.local
    """
    
    return {
        "ok": True,
        "message": f"Saved responses for {len(responses)} skills",
        "responses_count": len(responses)
    }

