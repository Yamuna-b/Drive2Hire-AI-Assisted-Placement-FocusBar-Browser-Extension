"""Phase 6: Coding Session Tracker for LeetCode, GeeksforGeeks, Codeforces"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import httpx
import os
from backend.db.database import get_db
from backend.models.coding_session import CodingSession
from backend.models.user import User

router = APIRouter()


class CodingProblem(BaseModel):
    """Represents a coding problem solved."""
    platform: str  # leetcode, gfg, codeforces
    problem_id: str
    problem_name: str
    topic: str  # arrays, strings, dp, graphs, trees, etc.
    difficulty: str  # Easy, Medium, Hard
    status: str  # accepted, attempted, skipped
    solve_time_minutes: Optional[int] = None
    submission_url: Optional[str] = None
    solved_date: Optional[datetime] = None


class CodingSessionRequest(BaseModel):
    """Request to log a coding session."""
    user_id: int
    platform: str
    problems_solved: List[CodingProblem]
    session_duration_minutes: int
    session_type: str  # "practice", "contest", "interview_prep"
    notes: Optional[str] = None


class CodingSessionStats(BaseModel):
    """User's coding statistics."""
    user_id: int
    total_problems_solved: int
    problems_by_platform: Dict[str, int]
    problems_by_difficulty: Dict[str, int]
    problems_by_topic: Dict[str, int]
    streak: int  # Days of consecutive coding
    total_hours: float
    avg_solve_time: float


@router.post("/session/log")
async def log_coding_session(request: CodingSessionRequest, db: Session = Depends(get_db)):
    """Log a coding session with problems solved."""
    
    user_id = request.user_id
    
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"error": f"User {user_id} not found"}
    
    try:
        session_record = CodingSession(
            user_id=user_id,
            platform=request.platform,
            session_type=request.session_type,
            duration_minutes=request.session_duration_minutes,
            problems_count=len(request.problems_solved),
            problems_solved=len([p for p in request.problems_solved if p.status == "accepted"]),
            problems_data=[p.dict() for p in request.problems_solved],
            notes=request.notes,
            session_date=datetime.utcnow()
        )
        db.add(session_record)
        db.commit()
        
        return {
            "ok": True,
            "session_id": session_record.id,
            "problems_logged": len(request.problems_solved),
            "problems_solved": session_record.problems_solved,
            "platform": request.platform
        }
    
    except Exception as e:
        db.rollback()
        return {"error": str(e)}


@router.get("/user/{user_id}/stats")
async def get_coding_stats(user_id: int, db: Session = Depends(get_db)):
    """Get comprehensive coding statistics for a user."""
    
    sessions = db.query(CodingSession).filter(
        CodingSession.user_id == user_id
    ).all()
    
    if not sessions:
        return {
            "user_id": user_id,
            "total_sessions": 0,
            "stats": None
        }
    
    # Calculate statistics
    total_problems = 0
    total_solved = 0
    total_minutes = 0
    problems_by_platform = {}
    problems_by_difficulty = {}
    problems_by_topic = {}
    solve_times = []
    
    for session in sessions:
        total_problems += session.problems_count
        total_solved += session.problems_solved
        total_minutes += session.duration_minutes
        
        # Platform stats
        platform = session.platform
        problems_by_platform[platform] = problems_by_platform.get(platform, 0) + session.problems_count
        
        # Parse problems data
        if session.problems_data:
            for problem in session.problems_data:
                # Difficulty
                diff = problem.get("difficulty", "Unknown")
                problems_by_difficulty[diff] = problems_by_difficulty.get(diff, 0) + 1
                
                # Topic
                topic = problem.get("topic", "Unknown")
                problems_by_topic[topic] = problems_by_topic.get(topic, 0) + 1
                
                # Solve time
                if problem.get("solve_time_minutes"):
                    solve_times.append(problem["solve_time_minutes"])
    
    # Calculate streak (consecutive days of coding)
    streak = calculate_coding_streak(sessions)
    
    avg_solve_time = sum(solve_times) / len(solve_times) if solve_times else 0
    
    return {
        "user_id": user_id,
        "total_sessions": len(sessions),
        "total_problems": total_problems,
        "total_solved": total_solved,
        "total_hours": round(total_minutes / 60, 1),
        "avg_session_duration": round(total_minutes / len(sessions), 1) if sessions else 0,
        "avg_solve_time": round(avg_solve_time, 1),
        "streak": streak,
        "problems_by_platform": problems_by_platform,
        "problems_by_difficulty": problems_by_difficulty,
        "problems_by_topic": problems_by_topic,
        "accuracy": round((total_solved / total_problems * 100), 1) if total_problems > 0 else 0,
    }


@router.get("/user/{user_id}/sessions")
async def get_user_sessions(
    user_id: int,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get recent coding sessions for a user."""
    
    sessions = db.query(CodingSession).filter(
        CodingSession.user_id == user_id
    ).order_by(CodingSession.session_date.desc()).limit(limit).all()
    
    return {
        "user_id": user_id,
        "sessions": [
            {
                "id": s.id,
                "platform": s.platform,
                "session_type": s.session_type,
                "duration_minutes": s.duration_minutes,
                "problems_count": s.problems_count,
                "problems_solved": s.problems_solved,
                "accuracy": round((s.problems_solved / s.problems_count * 100), 1) if s.problems_count > 0 else 0,
                "session_date": s.session_date.isoformat(),
                "notes": s.notes
            }
            for s in sessions
        ]
    }


@router.get("/user/{user_id}/topic-stats")
async def get_topic_stats(user_id: int, db: Session = Depends(get_db)):
    """Get topic-wise performance stats."""
    
    sessions = db.query(CodingSession).filter(
        CodingSession.user_id == user_id
    ).all()
    
    topic_stats = {}
    
    for session in sessions:
        if session.problems_data:
            for problem in session.problems_data:
                topic = problem.get("topic", "Unknown")
                if topic not in topic_stats:
                    topic_stats[topic] = {
                        "attempted": 0,
                        "solved": 0,
                        "difficulty_distribution": {},
                        "avg_time": []
                    }
                
                topic_stats[topic]["attempted"] += 1
                if problem.get("status") == "accepted":
                    topic_stats[topic]["solved"] += 1
                
                diff = problem.get("difficulty", "Unknown")
                topic_stats[topic]["difficulty_distribution"][diff] = \
                    topic_stats[topic]["difficulty_distribution"].get(diff, 0) + 1
                
                if problem.get("solve_time_minutes"):
                    topic_stats[topic]["avg_time"].append(problem["solve_time_minutes"])
    
    # Calculate averages
    for topic in topic_stats:
        times = topic_stats[topic]["avg_time"]
        topic_stats[topic]["avg_time"] = round(sum(times) / len(times), 1) if times else 0
        topic_stats[topic]["proficiency"] = round(
            (topic_stats[topic]["solved"] / topic_stats[topic]["attempted"] * 100), 1
        ) if topic_stats[topic]["attempted"] > 0 else 0
    
    return {
        "user_id": user_id,
        "topic_stats": topic_stats
    }


@router.get("/platform-parser/{platform}")
async def get_platform_parser_info(platform: str):
    """Get information about parsing/connecting a specific coding platform.
    
    Supports: leetcode, gfg, codeforces
    """
    
    parsers = {
        "leetcode": {
            "name": "LeetCode",
            "api_type": "GraphQL",
            "endpoint": "https://leetcode.com/graphql",
            "auth": "Uses session cookies",
            "capabilities": [
                "Get user profile",
                "Fetch solved problems",
                "Get problem details",
                "Parse submission history"
            ],
            "implementation": "Use LeetCode GraphQL API with session tokens",
            "rate_limit": "No strict limit but be respectful"
        },
        "gfg": {
            "name": "GeeksforGeeks",
            "api_type": "REST/Scraping",
            "endpoint": "https://practice.geeksforgeeks.org",
            "auth": "Username/Password or Session",
            "capabilities": [
                "Get user stats",
                "Fetch solved problems",
                "Parse difficulty levels",
                "Get category-wise stats"
            ],
            "implementation": "Use Selenium for scraping or GFG unofficial API",
            "rate_limit": "Respectful 1-2 requests per second"
        },
        "codeforces": {
            "name": "Codeforces",
            "api_type": "REST API",
            "endpoint": "https://codeforces.com/api",
            "auth": "Public API with optional auth",
            "capabilities": [
                "Get user info",
                "Fetch submissions",
                "Get problem details",
                "Access contests"
            ],
            "implementation": "Use official Codeforces API (REST)",
            "rate_limit": "1 request per 2 seconds per IP"
        }
    }
    
    if platform.lower() not in parsers:
        return {"error": f"Platform {platform} not supported"}
    
    return parsers[platform.lower()]


def calculate_coding_streak(sessions: List[CodingSession]) -> int:
    """Calculate current coding streak (consecutive days)."""
    
    if not sessions:
        return 0
    
    # Sort sessions by date (newest first)
    sorted_sessions = sorted(sessions, key=lambda s: s.session_date, reverse=True)
    
    streak = 1
    current_date = sorted_sessions[0].session_date.date()
    
    for i in range(1, len(sorted_sessions)):
        session_date = sorted_sessions[i].session_date.date()
        expected_date = current_date - timedelta(days=1)
        
        if session_date == expected_date:
            streak += 1
            current_date = session_date
        elif session_date < expected_date:
            break  # Streak broken
        # If session_date == current_date, continue (multiple sessions same day)
    
    return streak


@router.post("/sync/leetcode")
async def sync_leetcode_profile(user_id: int, username: str, db: Session = Depends(get_db)):
    """Sync LeetCode profile data using GraphQL API."""
    
    if not username:
        return {"error": "Username required"}
    
    try:
        # LeetCode GraphQL API endpoint
        query = """
        query getUserProfile($username: String!) {
            matchedUser(username: $username) {
                submitStats: submitStatsGlobal {
                    acSubmissionNum {
                        difficulty
                        count
                    }
                }
                profile {
                    realName
                    userAvatar
                    ranking
                }
            }
        }
        """
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                "https://leetcode.com/graphql",
                json={
                    "query": query,
                    "variables": {"username": username}
                },
                headers={"Content-Type": "application/json"}
            )
            data = response.json()
            
            if "errors" in data:
                return {"error": "User not found or API error", "details": data["errors"]}
            
            user_data = data["data"]["matchedUser"]
            submit_stats = user_data["submitStats"]["acSubmissionNum"]
            profile = user_data["profile"]
            
            # Extract problem counts by difficulty
            easy = next((s["count"] for s in submit_stats if s["difficulty"] == "Easy"), 0)
            medium = next((s["count"] for s in submit_stats if s["difficulty"] == "Medium"), 0)
            hard = next((s["count"] for s in submit_stats if s["difficulty"] == "Hard"), 0)
            total = easy + medium + hard
            
            # Create a session record for this sync
            session_record = CodingSession(
                user_id=user_id,
                platform="leetcode",
                session_type="sync",
                duration_minutes=0,
                problems_count=total,
                problems_solved=total,
                problems_data=[{
                    "platform": "leetcode",
                    "problem_id": "sync",
                    "problem_name": f"LeetCode Profile Sync - {username}",
                    "topic": "all",
                    "difficulty": "mixed",
                    "status": "accepted",
                    "solve_time_minutes": None,
                    "submission_url": f"https://leetcode.com/{username}"
                }],
                notes=f"Synced from LeetCode profile. Ranking: {profile.get('ranking', 'N/A')}",
                session_date=datetime.utcnow()
            )
            db.add(session_record)
            db.commit()
            
            return {
                "ok": True,
                "username": username,
                "total_solved": total,
                "easy": easy,
                "medium": medium,
                "hard": hard,
                "ranking": profile.get("ranking"),
                "real_name": profile.get("realName"),
                "synced_at": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        return {"error": str(e), "message": "Failed to sync LeetCode profile"}


@router.post("/sync/gfg")
async def sync_gfg_profile(user_id: int, username: str, db: Session = Depends(get_db)):
    """Sync GeeksforGeeks profile data using web scraping."""
    
    if not username:
        return {"error": "Username required"}
    
    try:
        # GFG doesn't have a public API, so we'll use web scraping
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"https://auth.geeksforgeeks.org/user/{username}",
                headers={"User-Agent": "Mozilla/5.0"}
            )
            
            if response.status_code != 200:
                return {"error": "Failed to fetch GFG profile", "status_code": response.status_code}
            
            html = response.text
            
            # Extract basic stats from HTML (this is a simplified approach)
            # In production, you'd use BeautifulSoup for proper parsing
            import re
            
            # Try to extract problem count from common patterns
            problems_match = re.search(r'(\d+)\s+problems?\s+solved', html, re.IGNORECASE)
            coding_score_match = re.search(r'coding\s+score[:\s]+(\d+)', html, re.IGNORECASE)
            
            problems_solved = int(problems_match.group(1)) if problems_match else 0
            coding_score = int(coding_score_match.group(1)) if coding_score_match else 0
            
            # Create a session record
            session_record = CodingSession(
                user_id=user_id,
                platform="gfg",
                session_type="sync",
                duration_minutes=0,
                problems_count=problems_solved,
                problems_solved=problems_solved,
                problems_data=[{
                    "platform": "gfg",
                    "problem_id": "sync",
                    "problem_name": f"GFG Profile Sync - {username}",
                    "topic": "all",
                    "difficulty": "mixed",
                    "status": "accepted",
                    "solve_time_minutes": None,
                    "submission_url": f"https://auth.geeksforgeeks.org/user/{username}"
                }],
                notes=f"Synced from GFG profile. Coding Score: {coding_score}",
                session_date=datetime.utcnow()
            )
            db.add(session_record)
            db.commit()
            
            return {
                "ok": True,
                "username": username,
                "problems_solved": problems_solved,
                "coding_score": coding_score,
                "synced_at": datetime.utcnow().isoformat(),
                "note": "Web scraping - may need BeautifulSoup for accurate data"
            }
            
    except Exception as e:
        return {"error": str(e), "message": "Failed to sync GFG profile"}


@router.post("/sync/codeforces")
async def sync_codeforces_profile(user_id: int, username: str, db: Session = Depends(get_db)):
    """Sync Codeforces profile data using official API."""
    
    if not username:
        return {"error": "Username required"}
    
    try:
        # Codeforces has a public API
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Get user info
            user_response = await client.get(
                f"https://codeforces.com/api/user.info?handles={username}"
            )
            user_data = user_response.json()
            
            if user_data["status"] != "OK":
                return {"error": "User not found on Codeforces"}
            
            user_info = user_data["result"][0]
            
            # Get user submissions
            submissions_response = await client.get(
                f"https://codeforces.com/api/user.status?handle={username}"
            )
            submissions_data = submissions_response.json()
            
            if submissions_data["status"] != "OK":
                return {"error": "Failed to fetch submissions"}
            
            submissions = submissions_data["result"]
            accepted = [s for s in submissions if s["verdict"] == "OK"]
            total_problems = len(accepted)
            
            # Count by rating (difficulty)
            difficulty_counts = {}
            for sub in accepted:
                rating = sub.get("problem", {}).get("rating", "Unknown")
                difficulty_counts[rating] = difficulty_counts.get(rating, 0) + 1
            
            # Create a session record
            session_record = CodingSession(
                user_id=user_id,
                platform="codeforces",
                session_type="sync",
                duration_minutes=0,
                problems_count=total_problems,
                problems_solved=total_problems,
                problems_data=[{
                    "platform": "codeforces",
                    "problem_id": "sync",
                    "problem_name": f"Codeforces Profile Sync - {username}",
                    "topic": "all",
                    "difficulty": "mixed",
                    "status": "accepted",
                    "solve_time_minutes": None,
                    "submission_url": f"https://codeforces.com/profile/{username}"
                }],
                notes=f"Synced from Codeforces. Rating: {user_info.get('rating', 'Unrated')}, Max: {user_info.get('maxRating', 'N/A')}",
                session_date=datetime.utcnow()
            )
            db.add(session_record)
            db.commit()
            
            return {
                "ok": True,
                "username": username,
                "rating": user_info.get("rating"),
                "max_rating": user_info.get("maxRating"),
                "rank": user_info.get("rank"),
                "total_problems_solved": total_problems,
                "difficulty_breakdown": difficulty_counts,
                "synced_at": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        return {"error": str(e), "message": "Failed to sync Codeforces profile"}
