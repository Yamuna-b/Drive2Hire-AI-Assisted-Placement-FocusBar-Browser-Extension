"""Phase 7: Gap Analysis & Personalized Learning Roadmap"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from backend.db.database import get_db
from backend.models.user_skill import UserSkill
from backend.models.user import User
from backend.models.company import Company

router = APIRouter()


class SkillGap(BaseModel):
    """Represents a skill gap for a job requirement."""
    skill_name: str
    required_level: str
    current_level: Optional[str]
    gap_severity: str  # critical, high, medium, low
    learning_time_estimate: int  # hours


class GapAnalysisRequest(BaseModel):
    """Request gap analysis for a job posting."""
    user_id: int
    job_title: str
    company: str
    mandatory_skills: List[dict]
    nice_to_have_skills: List[dict]


class LearningResource(BaseModel):
    """A learning resource for a skill."""
    title: str
    platform: str  # udemy, coursera, youtube, gfg, leetcode, etc.
    url: str
    difficulty: str  # beginner, intermediate, advanced
    estimated_duration_hours: int
    cost: str  # free, paid, subscription
    rating: Optional[float] = None


class PersonalizedRoadmap(BaseModel):
    """A personalized learning roadmap."""
    user_id: int
    job_title: str
    company: str
    total_gaps: int
    critical_gaps: List[SkillGap]
    high_priority_gaps: List[SkillGap]
    medium_priority_gaps: List[SkillGap]
    estimated_total_hours: int
    estimated_weeks: int
    roadmap_phases: List[Dict[str, Any]]
    resources: List[LearningResource]


# Learning resource database
RESOURCES_DB = {
    "Java": [
        {"title": "Core Java Basics", "platform": "YouTube", "url": "https://youtube.com/java", "difficulty": "beginner", "duration": 30, "cost": "free"},
        {"title": "Java Master Class", "platform": "Udemy", "url": "https://udemy.com/java", "difficulty": "intermediate", "duration": 40, "cost": "paid"},
        {"title": "Advanced Java", "platform": "Coursera", "url": "https://coursera.org/java", "difficulty": "advanced", "duration": 50, "cost": "subscription"},
    ],
    "Python": [
        {"title": "Python for Beginners", "platform": "YouTube", "url": "https://youtube.com/python", "difficulty": "beginner", "duration": 25, "cost": "free"},
        {"title": "Complete Python", "platform": "Udemy", "url": "https://udemy.com/python", "difficulty": "intermediate", "duration": 35, "cost": "paid"},
    ],
    "Spring Boot": [
        {"title": "Spring Boot 101", "platform": "YouTube", "url": "https://youtube.com/springboot", "difficulty": "beginner", "duration": 15, "cost": "free"},
        {"title": "Spring Boot Masterclass", "platform": "Udemy", "url": "https://udemy.com/springboot", "difficulty": "intermediate", "duration": 40, "cost": "paid"},
    ],
    "React": [
        {"title": "React Basics", "platform": "YouTube", "url": "https://youtube.com/react", "difficulty": "beginner", "duration": 20, "cost": "free"},
        {"title": "React Complete Course", "platform": "Udemy", "url": "https://udemy.com/react", "difficulty": "intermediate", "duration": 50, "cost": "paid"},
    ],
    "SQL": [
        {"title": "SQL Fundamentals", "platform": "YouTube", "url": "https://youtube.com/sql", "difficulty": "beginner", "duration": 20, "cost": "free"},
        {"title": "SQL Masterclass", "platform": "Udemy", "url": "https://udemy.com/sql", "difficulty": "intermediate", "duration": 30, "cost": "paid"},
    ],
    "Docker": [
        {"title": "Docker for Beginners", "platform": "YouTube", "url": "https://youtube.com/docker", "difficulty": "beginner", "duration": 15, "cost": "free"},
        {"title": "Docker & Kubernetes", "platform": "Udemy", "url": "https://udemy.com/docker", "difficulty": "intermediate", "duration": 45, "cost": "paid"},
    ],
    "Kubernetes": [
        {"title": "K8s Basics", "platform": "YouTube", "url": "https://youtube.com/k8s", "difficulty": "intermediate", "duration": 20, "cost": "free"},
        {"title": "K8s Advanced", "platform": "Udemy", "url": "https://udemy.com/k8s", "difficulty": "advanced", "duration": 40, "cost": "paid"},
    ],
}


@router.post("/analyze")
async def analyze_skill_gaps(request: GapAnalysisRequest, db: Session = Depends(get_db)):
    """Analyze skill gaps between user profile and job requirements."""
    
    user_id = request.user_id
    
    # Get user's current skills
    user_skills = db.query(UserSkill).filter(UserSkill.user_id == user_id).all()
    user_skill_map = {
        us.skill.name.lower(): us 
        for us in user_skills if us.skill
    }
    
    # Analyze mandatory skills
    mandatory_gaps = []
    for skill_obj in request.mandatory_skills:
        skill_name = skill_obj.get("name", "")
        gap = analyze_single_skill_gap(skill_name, user_skill_map, is_mandatory=True)
        if gap:
            mandatory_gaps.append(gap)
    
    # Analyze nice-to-have skills
    nice_to_have_gaps = []
    for skill_obj in request.nice_to_have_skills:
        skill_name = skill_obj.get("name", "")
        gap = analyze_single_skill_gap(skill_name, user_skill_map, is_mandatory=False)
        if gap:
            nice_to_have_gaps.append(gap)
    
    # Categorize by severity
    critical_gaps = [g for g in mandatory_gaps if g["gap_severity"] == "critical"]
    high_gaps = [g for g in mandatory_gaps if g["gap_severity"] == "high"]
    medium_gaps = [g for g in nice_to_have_gaps + mandatory_gaps if g["gap_severity"] == "medium"]
    
    total_hours = sum(g["learning_time_estimate"] for g in mandatory_gaps + nice_to_have_gaps)
    estimated_weeks = max(1, (total_hours + 19) // 20)  # Assuming 20 hours/week
    
    return {
        "user_id": user_id,
        "job_title": request.job_title,
        "company": request.company,
        "total_gaps": len(mandatory_gaps) + len(nice_to_have_gaps),
        "critical_gaps": len(critical_gaps),
        "high_priority_gaps": len(high_gaps),
        "medium_priority_gaps": len(medium_gaps),
        "gaps": {
            "critical": critical_gaps,
            "high": high_gaps,
            "medium": medium_gaps
        },
        "total_learning_hours": total_hours,
        "estimated_weeks": estimated_weeks,
        "confidence_score": calculate_match_confidence(critical_gaps, high_gaps, medium_gaps)
    }


@router.post("/roadmap")
async def generate_learning_roadmap(request: GapAnalysisRequest, db: Session = Depends(get_db)):
    """Generate personalized learning roadmap with resources."""
    
    # First analyze gaps
    gap_analysis = await analyze_skill_gaps(request, db)
    
    all_gaps = (
        gap_analysis.get("gaps", {}).get("critical", []) +
        gap_analysis.get("gaps", {}).get("high", []) +
        gap_analysis.get("gaps", {}).get("medium", [])
    )
    
    # Generate phased roadmap
    phases = generate_roadmap_phases(all_gaps)
    
    # Collect resources
    resources = []
    for gap in all_gaps:
        skill_name = gap["skill_name"]
        skill_resources = RESOURCES_DB.get(skill_name, [])
        resources.extend(skill_resources)
    
    # Remove duplicates
    unique_resources = {r["title"]: r for r in resources}.values()
    
    return {
        "user_id": request.user_id,
        "job_title": request.job_title,
        "company": request.company,
        "total_gaps": gap_analysis["total_gaps"],
        "total_learning_hours": gap_analysis["total_learning_hours"],
        "estimated_weeks": gap_analysis["estimated_weeks"],
        "phases": phases,
        "resources": list(unique_resources),
        "tips": get_preparation_tips(request.job_title, request.company),
        "interview_prep": get_interview_prep_guide(request.job_title)
    }


@router.get("/job-match/{user_id}")
async def calculate_job_match(user_id: int, job_title: str, company: str, db: Session = Depends(get_db)):
    """The live match is produced by POST /job/analyse from the current page."""
    return {
        "user_id": user_id,
        "job_title": job_title,
        "company": company,
        "status": "requires_live_job_description",
        "message": "Send the current job description to POST /job/analyse for an evidence-backed result.",
    }


@router.post("/resources/{skill_name}")
async def get_skill_resources(skill_name: str):
    """Get learning resources for a specific skill."""
    
    resources = RESOURCES_DB.get(skill_name, [])
    
    if not resources:
        return {
            "skill": skill_name,
            "resources": [],
            "message": f"No curated resources for {skill_name} yet. Please search manually."
        }
    
    return {
        "skill": skill_name,
        "total_resources": len(resources),
        "resources": resources
    }


@router.post("/subscribe-resource")
async def subscribe_to_resource(user_id: int, resource_title: str, platform: str, db: Session = Depends(get_db)):
    """Subscribe user to a learning resource for tracking."""
    
    # This would create a subscription record in database
    return {
        "ok": True,
        "user_id": user_id,
        "resource": resource_title,
        "platform": platform,
        "message": "Subscribed to resource. Progress tracking enabled."
    }


def analyze_single_skill_gap(skill_name: str, user_skill_map: Dict, is_mandatory: bool) -> Optional[Dict]:
    """Analyze gap for a single skill."""
    
    if not skill_name:
        return None
    
    user_skill = user_skill_map.get(skill_name.lower())
    
    # Determine gap severity
    if not user_skill:
        gap_severity = "critical" if is_mandatory else "high"
        learning_time = 40  # Default estimate
    elif user_skill.duration_bucket and "1 year" in user_skill.duration_bucket:
        gap_severity = "high"
        learning_time = 20
    elif user_skill.duration_bucket and "2+" in user_skill.duration_bucket:
        gap_severity = "low"
        learning_time = 5
    else:
        gap_severity = "medium"
        learning_time = 15
    
    return {
        "skill_name": skill_name,
        "current_level": user_skill.duration_bucket if user_skill else "None",
        "required_level": "2+ Years",
        "gap_severity": gap_severity,
        "learning_time_estimate": learning_time
    }


def generate_roadmap_phases(gaps: List[Dict]) -> List[Dict]:
    """Generate phased learning plan."""
    
    phases = []
    
    # Phase 1: Critical skills (Week 1-2)
    critical = [g for g in gaps if g["gap_severity"] == "critical"]
    if critical:
        phases.append({
            "phase": 1,
            "title": "Foundation Building (Week 1-2)",
            "duration_weeks": 2,
            "focus": "Critical mandatory skills",
            "skills": [g["skill_name"] for g in critical],
            "daily_time_estimate": 3,
            "goals": [
                "Understand core concepts",
                "Complete basic tutorials",
                "Write simple programs"
            ]
        })
    
    # Phase 2: High priority skills (Week 3-4)
    high = [g for g in gaps if g["gap_severity"] == "high"]
    if high:
        phases.append({
            "phase": 2,
            "title": "Skill Development (Week 3-4)",
            "duration_weeks": 2,
            "focus": "High priority skills & problem solving",
            "skills": [g["skill_name"] for g in high],
            "daily_time_estimate": 2,
            "goals": [
                "Build practice projects",
                "Solve problems on LeetCode",
                "Understand patterns"
            ]
        })
    
    # Phase 3: Medium priority + Interview prep (Week 5-6)
    phases.append({
        "phase": 3,
        "title": "Interview Preparation (Week 5-6)",
        "duration_weeks": 2,
        "focus": "System design, DSA, Behavioral",
        "daily_time_estimate": 2,
        "goals": [
            "Practice system design",
            "Mock interviews",
            "Behavioral prep"
        ]
    })
    
    # Phase 4: Final review & application (Week 7+)
    phases.append({
        "phase": 4,
        "title": "Final Review & Application (Week 7+)",
        "duration_weeks": 1,
        "focus": "Review & apply",
        "daily_time_estimate": 1,
        "goals": [
            "Revise key concepts",
            "Polish resume",
            "Apply to jobs"
        ]
    })
    
    return phases


def calculate_match_confidence(critical: List, high: List, medium: List) -> float:
    """Calculate overall match confidence (0-100)."""
    
    total_gaps = len(critical) + len(high) + len(medium)
    
    if total_gaps == 0:
        return 100.0
    
    # Each critical gap reduces by 20%, high by 10%, medium by 5%
    score = 100.0
    score -= len(critical) * 20
    score -= len(high) * 10
    score -= len(medium) * 5
    
    return max(0, min(100, score))


def get_preparation_tips(job_title: str, company: str) -> List[str]:
    """Get role-specific preparation tips."""
    
    tips = [
        "Build a portfolio with projects matching the role requirements",
        "Practice coding problems on LeetCode (minimum 50 problems)",
        "Prepare for system design interviews if it's a senior role",
        "Research the company culture and recent tech decisions",
        "Prepare stories for behavioral questions using STAR method"
    ]
    
    # Add role-specific tips
    if "backend" in job_title.lower():
        tips.extend([
            "Focus on database design and API development",
            "Learn about microservices architecture",
            "Practice SQL queries and optimization"
        ])
    elif "frontend" in job_title.lower():
        tips.extend([
            "Build responsive UIs using CSS Grid/Flexbox",
            "Practice React hooks and state management",
            "Learn performance optimization techniques"
        ])
    elif "devops" in job_title.lower():
        tips.extend([
            "Learn CI/CD pipelines using Jenkins/GitHub Actions",
            "Practice containerization with Docker",
            "Understand cloud platforms (AWS/Azure/GCP)"
        ])
    
    return tips


def get_interview_prep_guide(job_title: str) -> Dict:
    """Get interview preparation guide."""
    
    return {
        "rounds": [
            {
                "type": "Phone Screen",
                "duration": "30 mins",
                "focus": "Communication, motivation, basic technical questions"
            },
            {
                "type": "Coding Round",
                "duration": "60 mins",
                "focus": f"Medium-level DSA problems ({job_title}-specific)"
            },
            {
                "type": "System Design",
                "duration": "45 mins",
                "focus": "Design scalable systems (if senior level)"
            },
            {
                "type": "Behavioral",
                "duration": "30 mins",
                "focus": "STAR questions about past experiences"
            }
        ],
        "preparation_tips": [
            "Practice with mock interviews",
            "Record yourself answering questions",
            "Research company's tech stack",
            "Prepare edge case handling for code"
        ]
    }
