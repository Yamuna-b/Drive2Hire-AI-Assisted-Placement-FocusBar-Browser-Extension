"""Phase 8: Application Outcome Tracking & Analytics Dashboard"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from backend.db.database import get_db
from backend.models.application import Application
from backend.models.user import User

router = APIRouter()


class ApplicationRecord(BaseModel):
    """Application tracking record."""
    user_id: int
    job_title: str
    company: str
    application_status: str  # applied, shortlisted, interviewed, rejected, offered
    application_date: datetime
    jd_url: Optional[str] = None
    match_score: Optional[int] = None
    notes: Optional[str] = None


class ApplicationUpdate(BaseModel):
    """Update application status."""
    user_id: int
    application_id: int
    new_status: str
    follow_up_date: Optional[datetime] = None
    notes: Optional[str] = None
    interview_date: Optional[datetime] = None


class ApplicationAnalytics(BaseModel):
    """Analytics for applications."""
    user_id: int
    total_applications: int
    status_distribution: Dict[str, int]
    success_rate: float
    average_time_to_response: int  # days
    conversion_funnel: Dict[str, float]


@router.post("/track")
async def track_application(record: ApplicationRecord, db: Session = Depends(get_db)):
    """Track a new job application."""
    
    user_id = record.user_id
    
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"error": f"User {user_id} not found"}
    
    try:
        application = Application(
            user_id=user_id,
            job_title=record.job_title,
            company=record.company,
            status=record.application_status or "applied",
            application_date=record.application_date or datetime.utcnow(),
            jd_url=record.jd_url,
            match_score=record.match_score,
            notes=record.notes
        )
        db.add(application)
        db.commit()
        
        return {
            "ok": True,
            "application_id": application.id,
            "company": record.company,
            "job_title": record.job_title,
            "status": record.application_status,
            "application_date": application.application_date.isoformat()
        }
    
    except Exception as e:
        db.rollback()
        return {"error": str(e)}


@router.put("/update/{application_id}")
async def update_application_status(
    application_id: int,
    update: ApplicationUpdate,
    db: Session = Depends(get_db)
):
    """Update application status."""
    
    try:
        application = db.query(Application).filter(
            Application.id == application_id,
            Application.user_id == update.user_id
        ).first()
        
        if not application:
            return {"error": "Application not found"}
        
        # Update fields
        application.status = update.new_status
        if update.notes:
            application.notes = update.notes
        if update.follow_up_date:
            application.follow_up_date = update.follow_up_date
        if update.interview_date:
            application.interview_date = update.interview_date
        
        application.last_updated = datetime.utcnow()
        
        db.commit()
        
        return {
            "ok": True,
            "application_id": application_id,
            "new_status": update.new_status,
            "last_updated": application.last_updated.isoformat()
        }
    
    except Exception as e:
        db.rollback()
        return {"error": str(e)}


@router.get("/user/{user_id}/applications")
async def get_user_applications(user_id: int, db: Session = Depends(get_db)):
    """Get all applications for a user."""
    
    applications = db.query(Application).filter(
        Application.user_id == user_id
    ).order_by(Application.application_date.desc()).all()
    
    if not applications:
        return {
            "user_id": user_id,
            "total_applications": 0,
            "applications": []
        }
    
    return {
        "user_id": user_id,
        "total_applications": len(applications),
        "applications": [
            {
                "id": app.id,
                "job_title": app.job_title,
                "company": app.company,
                "status": app.status,
                "application_date": app.application_date.isoformat(),
                "match_score": app.match_score,
                "interview_date": app.interview_date.isoformat() if app.interview_date else None,
                "notes": app.notes,
                "days_since_application": (datetime.utcnow() - app.application_date).days
            }
            for app in applications
        ]
    }


@router.get("/user/{user_id}/analytics")
async def get_application_analytics(user_id: int, db: Session = Depends(get_db)):
    """Get analytics for user's applications."""
    
    applications = db.query(Application).filter(
        Application.user_id == user_id
    ).all()
    
    if not applications:
        return {
            "user_id": user_id,
            "total_applications": 0,
            "analytics": None
        }
    
    # Calculate status distribution
    status_distribution = {
        "applied": 0,
        "shortlisted": 0,
        "interviewed": 0,
        "rejected": 0,
        "offered": 0
    }
    
    for app in applications:
        status = app.status.lower()
        if status in status_distribution:
            status_distribution[status] += 1
    
    # Calculate success metrics
    total = len(applications)
    shortlisted = status_distribution["shortlisted"] + status_distribution["interviewed"] + status_distribution["offered"]
    offered = status_distribution["offered"]
    
    success_rate = (offered / total * 100) if total > 0 else 0
    conversion_funnel = {
        "applied_to_shortlist": (shortlisted / total * 100) if total > 0 else 0,
        "shortlist_to_interview": (status_distribution["interviewed"] / shortlisted * 100) if shortlisted > 0 else 0,
        "interview_to_offer": (offered / status_distribution["interviewed"] * 100) if status_distribution["interviewed"] > 0 else 0,
    }
    
    # Calculate average response time
    response_times = []
    for app in applications:
        if app.follow_up_date and app.application_date:
            days = (app.follow_up_date - app.application_date).days
            response_times.append(days)
    
    avg_response_time = (sum(response_times) // len(response_times)) if response_times else 0
    
    return {
        "user_id": user_id,
        "total_applications": total,
        "status_distribution": status_distribution,
        "success_rate": round(success_rate, 2),
        "average_response_days": avg_response_time,
        "conversion_funnel": {k: round(v, 2) for k, v in conversion_funnel.items()},
        "offers": offered,
        "interview_stage_count": status_distribution["interviewed"]
    }


@router.get("/user/{user_id}/pipeline")
async def get_application_pipeline(user_id: int, db: Session = Depends(get_db)):
    """Get applications in each pipeline stage (Kanban-like view)."""
    
    applications = db.query(Application).filter(
        Application.user_id == user_id
    ).order_by(Application.application_date.desc()).all()
    
    pipeline = {
        "applied": [],
        "shortlisted": [],
        "interviewed": [],
        "rejected": [],
        "offered": []
    }
    
    for app in applications:
        status = app.status.lower()
        if status in pipeline:
            pipeline[status].append({
                "id": app.id,
                "company": app.company,
                "job_title": app.job_title,
                "match_score": app.match_score,
                "days_in_stage": (datetime.utcnow() - app.application_date).days,
                "interview_date": app.interview_date.isoformat() if app.interview_date else None
            })
    
    return {
        "user_id": user_id,
        "pipeline": pipeline
    }


@router.get("/user/{user_id}/company-stats")
async def get_company_statistics(user_id: int, db: Session = Depends(get_db)):
    """Get statistics by company."""
    
    applications = db.query(Application).filter(
        Application.user_id == user_id
    ).all()
    
    company_stats = {}
    
    for app in applications:
        company = app.company
        if company not in company_stats:
            company_stats[company] = {
                "applications": 0,
                "statuses": {},
                "avg_match_score": 0,
                "highest_match": 0
            }
        
        company_stats[company]["applications"] += 1
        
        status = app.status.lower()
        company_stats[company]["statuses"][status] = company_stats[company]["statuses"].get(status, 0) + 1
        
        if app.match_score:
            company_stats[company]["highest_match"] = max(
                company_stats[company]["highest_match"],
                app.match_score
            )
    
    # Calculate averages
    for company in company_stats:
        matches = [
            app.match_score for app in applications
            if app.company == company and app.match_score
        ]
        if matches:
            company_stats[company]["avg_match_score"] = round(sum(matches) / len(matches), 1)
    
    return {
        "user_id": user_id,
        "company_stats": company_stats
    }


@router.get("/user/{user_id}/timeline")
async def get_application_timeline(user_id: int, db: Session = Depends(get_db)):
    """Get timeline view of applications."""
    
    applications = db.query(Application).filter(
        Application.user_id == user_id
    ).order_by(Application.application_date).all()
    
    timeline = []
    
    for app in applications:
        timeline.append({
            "date": app.application_date.isoformat(),
            "event": f"Applied to {app.company} - {app.job_title}",
            "company": app.company,
            "status": app.status,
            "match_score": app.match_score
        })
        
        if app.follow_up_date:
            timeline.append({
                "date": app.follow_up_date.isoformat(),
                "event": f"Status update: {app.status}",
                "company": app.company,
                "status": app.status
            })
        
        if app.interview_date:
            timeline.append({
                "date": app.interview_date.isoformat(),
                "event": f"Interview scheduled at {app.company}",
                "company": app.company,
                "type": "interview"
            })
    
    return {
        "user_id": user_id,
        "total_events": len(timeline),
        "timeline": timeline
    }


@router.post("/user/{user_id}/export")
async def export_applications(user_id: int, format: str = "csv", db: Session = Depends(get_db)):
    """Export applications data."""
    
    applications = db.query(Application).filter(
        Application.user_id == user_id
    ).all()
    
    if not applications:
        return {"error": "No applications to export"}
    
    if format == "csv":
        return {
            "format": "csv",
            "columns": ["Company", "Job Title", "Status", "Application Date", "Match Score", "Notes"],
            "data": [
                [
                    app.company,
                    app.job_title,
                    app.status,
                    app.application_date.strftime("%Y-%m-%d"),
                    app.match_score or "N/A",
                    app.notes or ""
                ]
                for app in applications
            ]
        }
    
    elif format == "json":
        return {
            "format": "json",
            "applications": [
                {
                    "id": app.id,
                    "company": app.company,
                    "job_title": app.job_title,
                    "status": app.status,
                    "application_date": app.application_date.isoformat(),
                    "match_score": app.match_score,
                    "notes": app.notes
                }
                for app in applications
            ]
        }
    
    else:
        return {"error": "Unsupported format"}


@router.get("/insights/{user_id}")
async def get_placement_insights(user_id: int, db: Session = Depends(get_db)):
    """Get AI-powered insights and recommendations."""
    
    applications = db.query(Application).filter(
        Application.user_id == user_id
    ).all()
    
    if not applications:
        return {"insights": []}
    
    insights = []
    
    # Calculate metrics
    total = len(applications)
    offered = len([a for a in applications if a.status.lower() == "offered"])
    rejected = len([a for a in applications if a.status.lower() == "rejected"])
    
    # Insight 1: Success rate
    success_rate = (offered / total * 100) if total > 0 else 0
    if success_rate > 20:
        insights.append({
            "type": "positive",
            "title": "Strong Success Rate",
            "message": f"Congratulations! Your success rate ({success_rate:.1f}%) is above average. Keep applying to similar roles."
        })
    elif success_rate > 5:
        insights.append({
            "type": "neutral",
            "title": "Moderate Success Rate",
            "message": f"Your success rate ({success_rate:.1f}%) is reasonable. Focus on improving skill matches for better results."
        })
    else:
        insights.append({
            "type": "warning",
            "title": "Low Success Rate",
            "message": "Your success rate is low. Consider: (1) Taking more coding practice, (2) Improving resume, (3) Targeting roles with closer skill match"
        })
    
    # Insight 2: Application volume
    if total < 5:
        insights.append({
            "type": "warning",
            "title": "Low Application Volume",
            "message": "You've applied to fewer jobs. Increase your applications to improve chances of getting offers."
        })
    else:
        insights.append({
            "type": "positive",
            "title": "Good Application Volume",
            "message": f"You're maintaining good momentum with {total} applications."
        })
    
    # Insight 3: Top companies
    company_count = {}
    for app in applications:
        company_count[app.company] = company_count.get(app.company, 0) + 1
    
    top_company = max(company_count, key=company_count.get) if company_count else None
    if top_company:
        top_company_success = len([
            a for a in applications
            if a.company == top_company and a.status.lower() in ["offered", "interviewed"]
        ])
        insights.append({
            "type": "info",
            "title": f"Focus Area: {top_company}",
            "message": f"You've applied to {top_company} {company_count[top_company]} times. Success count: {top_company_success}"
        })
    
    return {"user_id": user_id, "insights": insights}
