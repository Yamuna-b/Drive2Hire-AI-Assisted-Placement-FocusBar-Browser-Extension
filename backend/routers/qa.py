from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

from backend.db.database import get_db
from backend.models.user import User
from backend.models.user_skill import UserSkill
from backend.models.skill import Skill
from backend.models.qa_response import QAResponse

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
    job_title: str | None = None
    job_company: str | None = None


class QASessionRequest(BaseModel):
    """Request Q&A session for gap skills."""
    mandatory_skills: List[dict]
    nice_to_have_skills: List[dict]
    user_skills: List[dict]
    user_id: Optional[int] = None  # For authenticated users


class BulkSkillUpdateRequest(BaseModel):
    """Bulk update multiple skills from Q&A session."""
    user_id: int
    skills: List[UserSkillResponse]


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
async def save_qa_responses(responses: List[UserSkillResponse], db: Session = Depends(get_db)):
    """Save user's Q&A responses to database and update user skills."""
    
    if not responses:
        return {"ok": True, "message": "No responses to save", "responses_count": 0}
    
    try:
        # Get or create user (for now, use user_id=1 as default)
        user_id = 1
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            user = User(id=user_id, name="Default User", email="user@example.com")
            db.add(user)
            db.commit()
        
        saved_responses = []
        
        for response in responses:
            # Save QA response
            qa_record = QAResponse(
                user_id=user_id,
                skill_name=response.skill_name,
                has_experience=response.has_experience,
                duration_bucket=response.duration_bucket if response.has_experience else None,
                project_notes=response.project_notes,
                job_title=response.job_title,
                job_company=response.job_company,
            )
            db.add(qa_record)
            
            # If user has experience, update/create UserSkill
            if response.has_experience:
                # Find or create skill
                skill = db.query(Skill).filter(
                    Skill.name.ilike(response.skill_name)
                ).first()
                
                if not skill:
                    skill = Skill(name=response.skill_name)
                    db.add(skill)
                    db.flush()
                
                # Find or create user_skill
                user_skill = db.query(UserSkill).filter(
                    UserSkill.user_id == user_id,
                    UserSkill.skill_id == skill.id
                ).first()
                
                if not user_skill:
                    user_skill = UserSkill(
                        user_id=user_id,
                        skill_id=skill.id,
                        duration_bucket=response.duration_bucket,
                        project_notes=response.project_notes,
                    )
                    db.add(user_skill)
                else:
                    # Update existing
                    user_skill.duration_bucket = response.duration_bucket
                    user_skill.project_notes = response.project_notes
            
            saved_responses.append(response.dict())
        
        db.commit()
        
        return {
            "ok": True,
            "message": f"Saved responses for {len(responses)} skills",
            "responses_count": len(responses),
            "saved_responses": saved_responses
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bulk-update-skills")
async def bulk_update_skills(request: BulkSkillUpdateRequest, db: Session = Depends(get_db)):
    """Bulk update user skills from Q&A session with database persistence."""
    
    user_id = request.user_id
    skills = request.skills
    
    if not skills:
        return {"ok": True, "message": "No skills to update"}
    
    try:
        updated_count = 0
        
        for skill_response in skills:
            if not skill_response.has_experience:
                continue
            
            # Find or create skill
            skill = db.query(Skill).filter(
                Skill.name.ilike(skill_response.skill_name)
            ).first()
            
            if not skill:
                skill = Skill(name=skill_response.skill_name)
                db.add(skill)
                db.flush()
            
            # Find or create user_skill
            user_skill = db.query(UserSkill).filter(
                UserSkill.user_id == user_id,
                UserSkill.skill_id == skill.id
            ).first()
            
            if not user_skill:
                user_skill = UserSkill(
                    user_id=user_id,
                    skill_id=skill.id,
                    duration_bucket=skill_response.duration_bucket,
                    project_notes=skill_response.project_notes,
                )
                db.add(user_skill)
            else:
                user_skill.duration_bucket = skill_response.duration_bucket
                user_skill.project_notes = skill_response.project_notes
            
            # Save QA response
            qa_record = QAResponse(
                user_id=user_id,
                user_skill_id=user_skill.id,
                skill_name=skill_response.skill_name,
                has_experience=True,
                duration_bucket=skill_response.duration_bucket,
                project_notes=skill_response.project_notes,
                job_title=skill_response.job_title,
                job_company=skill_response.job_company,
            )
            db.add(qa_record)
            updated_count += 1
        
        db.commit()
        
        return {
            "ok": True,
            "message": f"Updated {updated_count} skills",
            "updated_count": updated_count
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{user_id}/responses")
async def get_user_responses(user_id: int, db: Session = Depends(get_db)):
    """Get all Q&A responses for a user."""
    
    responses = db.query(QAResponse).filter(QAResponse.user_id == user_id).all()
    
    return {
        "user_id": user_id,
        "total_responses": len(responses),
        "responses": [r.to_dict() for r in responses]
    }


@router.get("/user/{user_id}/skills")
async def get_user_skills(user_id: int, db: Session = Depends(get_db)):
    """Get all user skills with Q&A history."""
    
    user_skills = db.query(UserSkill).filter(UserSkill.user_id == user_id).all()
    
    skills_data = []
    for us in user_skills:
        skill_name = us.skill.name if us.skill else "Unknown"
        qa_history = db.query(QAResponse).filter(
            QAResponse.user_skill_id == us.id
        ).order_by(QAResponse.answered_at.desc()).all()
        
        skills_data.append({
            "skill_id": us.id,
            "skill_name": skill_name,
            "duration_bucket": us.duration_bucket,
            "project_notes": us.project_notes,
            "qa_history_count": len(qa_history),
            "last_qa_date": qa_history[0].answered_at if qa_history else None
        })
    
    return {
        "user_id": user_id,
        "total_skills": len(skills_data),
        "skills": skills_data
    }

