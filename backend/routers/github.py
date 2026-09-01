"""GitHub API integration for profile stats"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
import httpx
import os

router = APIRouter()


class GitHubProfileResponse(BaseModel):
    """GitHub profile data."""
    username: str
    name: Optional[str]
    bio: Optional[str]
    public_repos: int
    followers: int
    following: int
    avatar_url: Optional[str]
    location: Optional[str]
    company: Optional[str]
    blog: Optional[str]


class GitHubRepoStats(BaseModel):
    """GitHub repository statistics."""
    total_repos: int
    languages: dict
    stars: int
    forks: int


@router.get("/profile/{username}")
async def get_github_profile(username: str):
    """Fetch GitHub profile data using public API."""
    
    if not username:
        return {"error": "Username required"}
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Get user profile
            response = await client.get(
                f"https://api.github.com/users/{username}",
                headers={
                    "Accept": "application/vnd.github.v3+json",
                    "User-Agent": "Drive2Hire-Extension"
                }
            )
            
            if response.status_code == 404:
                return {"error": "User not found on GitHub"}
            
            if response.status_code != 200:
                return {"error": f"GitHub API error: {response.status_code}"}
            
            user_data = response.json()
            
            return {
                "username": user_data.get("login"),
                "name": user_data.get("name"),
                "bio": user_data.get("bio"),
                "public_repos": user_data.get("public_repos", 0),
                "followers": user_data.get("followers", 0),
                "following": user_data.get("following", 0),
                "avatar_url": user_data.get("avatar_url"),
                "location": user_data.get("location"),
                "company": user_data.get("company"),
                "blog": user_data.get("blog"),
                "created_at": user_data.get("created_at"),
                "updated_at": user_data.get("updated_at")
            }
            
    except Exception as e:
        return {"error": str(e), "message": "Failed to fetch GitHub profile"}


@router.get("/repos/{username}")
async def get_github_repos(username: str):
    """Fetch GitHub repositories and language statistics."""
    
    if not username:
        return {"error": "Username required"}
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Get user's repositories
            response = await client.get(
                f"https://api.github.com/users/{username}/repos?per_page=100&sort=updated",
                headers={
                    "Accept": "application/vnd.github.v3+json",
                    "User-Agent": "Drive2Hire-Extension"
                }
            )
            
            if response.status_code != 200:
                return {"error": f"Failed to fetch repositories: {response.status_code}"}
            
            repos = response.json()
            
            # Calculate language statistics
            languages = {}
            total_stars = 0
            total_forks = 0
            
            for repo in repos:
                lang = repo.get("language")
                if lang:
                    languages[lang] = languages.get(lang, 0) + 1
                
                total_stars += repo.get("stargazers_count", 0)
                total_forks += repo.get("forks_count", 0)
            
            return {
                "username": username,
                "total_repos": len(repos),
                "languages": languages,
                "stars": total_stars,
                "forks": total_forks,
                "top_repos": [
                    {
                        "name": repo.get("name"),
                        "description": repo.get("description"),
                        "language": repo.get("language"),
                        "stars": repo.get("stargazers_count"),
                        "forks": repo.get("forks_count"),
                        "url": repo.get("html_url")
                    }
                    for repo in repos[:5]
                ]
            }
            
    except Exception as e:
        return {"error": str(e), "message": "Failed to fetch GitHub repositories"}


@router.get("/activity/{username}")
async def get_github_activity(username: str):
    """Fetch recent GitHub activity."""
    
    if not username:
        return {"error": "Username required"}
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Get recent events
            response = await client.get(
                f"https://api.github.com/users/{username}/events/public?per_page=10",
                headers={
                    "Accept": "application/vnd.github.v3+json",
                    "User-Agent": "Drive2Hire-Extension"
                }
            )
            
            if response.status_code != 200:
                return {"error": f"Failed to fetch activity: {response.status_code}"}
            
            events = response.json()
            
            activity_summary = {
                "push_events": 0,
                "pull_requests": 0,
                "issues": 0,
                "fork_events": 0,
                "recent_activity": []
            }
            
            for event in events[:10]:
                event_type = event.get("type")
                
                if event_type == "PushEvent":
                    activity_summary["push_events"] += 1
                elif event_type == "PullRequestEvent":
                    activity_summary["pull_requests"] += 1
                elif event_type == "IssuesEvent":
                    activity_summary["issues"] += 1
                elif event_type == "ForkEvent":
                    activity_summary["fork_events"] += 1
                
                activity_summary["recent_activity"].append({
                    "type": event_type,
                    "repo": event.get("repo", {}).get("name"),
                    "created_at": event.get("created_at")
                })
            
            return activity_summary
            
    except Exception as e:
        return {"error": str(e), "message": "Failed to fetch GitHub activity"}


@router.get("/test")
async def test():
    return {"msg": "github router works"}
