from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy import select

from backend.db.database import AsyncSessionLocal

# In-memory storage fallback when DB is not configured
_CODING_SESSIONS: List[Dict[str, Any]] = [
    {
        "id": 1,
        "user_id": 1,
        "platform": "LeetCode",
        "problem_id": "two-sum",
        "problem_title": "Two Sum",
        "difficulty": "Easy",
        "topics": ["Arrays", "Hash Table"],
        "duration_seconds": 900,
        "solved": True,
        "created_at": datetime.utcnow().isoformat()
    },
    {
        "id": 2,
        "user_id": 1,
        "platform": "LeetCode",
        "problem_id": "lru-cache",
        "problem_title": "LRU Cache",
        "difficulty": "Medium",
        "topics": ["Hash Table", "Linked List", "Design"],
        "duration_seconds": 1800,
        "solved": True,
        "created_at": datetime.utcnow().isoformat()
    },
    {
        "id": 3,
        "user_id": 1,
        "platform": "GeeksforGeeks",
        "problem_id": "binary-tree-inorder-traversal",
        "problem_title": "Inorder Traversal",
        "difficulty": "Easy",
        "topics": ["Trees", "Binary Tree", "DFS"],
        "duration_seconds": 1200,
        "solved": True,
        "created_at": datetime.utcnow().isoformat()
    }
]

_ACCOUNT_SYNCS: Dict[str, Dict[str, Any]] = {
    "leetcode": {
        "platform": "LeetCode",
        "handle": "student_coder",
        "total_solved": 45,
        "topic_breakdown": {
            "Arrays": 15,
            "Strings": 10,
            "Trees": 8,
            "Linked List": 6,
            "Dynamic Programming": 4,
            "Hash Table": 12
        },
        "last_synced_at": datetime.utcnow().isoformat()
    }
}


def log_session_memory(session_data: dict) -> dict:
    session_entry = {
        "id": len(_CODING_SESSIONS) + 1,
        "user_id": session_data.get("user_id", 1),
        "platform": session_data.get("platform", "Generic"),
        "problem_id": session_data.get("problem_id", ""),
        "problem_title": session_data.get("problem_title", "Practice Problem"),
        "difficulty": session_data.get("difficulty", "Medium"),
        "topics": session_data.get("topics", []),
        "duration_seconds": session_data.get("duration_seconds", 0),
        "solved": session_data.get("solved", True),
        "created_at": datetime.utcnow().isoformat()
    }
    _CODING_SESSIONS.append(session_entry)
    return session_entry


def sync_account_memory(platform: str, handle: str, total_solved: int = 0, topic_breakdown: dict = None) -> dict:
    platform_key = platform.lower()
    entry = {
        "platform": platform,
        "handle": handle,
        "total_solved": total_solved or 30,
        "topic_breakdown": topic_breakdown or {
            "Arrays": 10,
            "Strings": 8,
            "Trees": 5,
            "Linked List": 4,
            "Hash Table": 7
        },
        "last_synced_at": datetime.utcnow().isoformat()
    }
    _ACCOUNT_SYNCS[platform_key] = entry
    return entry


def get_coding_summary(user_id: int = 1) -> dict:
    """Aggregate stats from logged sessions and synced accounts."""
    difficulty_counts = {"Easy": 0, "Medium": 0, "Hard": 0}
    topic_distribution: Dict[str, int] = {}
    total_time_seconds = 0
    total_session_solved = 0

    # 1. Sum up session logs
    for s in _CODING_SESSIONS:
        if s.get("user_id") == user_id:
            diff = s.get("difficulty", "Medium").capitalize()
            if diff in difficulty_counts:
                difficulty_counts[diff] += 1
            else:
                difficulty_counts["Medium"] += 1

            if s.get("solved", True):
                total_session_solved += 1

            total_time_seconds += s.get("duration_seconds", 0)

            for t in s.get("topics", []):
                t_clean = t.strip().title()
                topic_distribution[t_clean] = topic_distribution.get(t_clean, 0) + 1

    # 2. Merge account sync stats
    synced_total = 0
    synced_accounts = list(_ACCOUNT_SYNCS.values())
    for acc in synced_accounts:
        synced_total += acc.get("total_solved", 0)
        for t, count in (acc.get("topic_breakdown") or {}).items():
            t_clean = t.strip().title()
            topic_distribution[t_clean] = max(topic_distribution.get(t_clean, 0), count)

    total_problems_solved = max(total_session_solved, synced_total)
    if synced_total > 0 and total_session_solved > 0:
        total_problems_solved = synced_total + total_session_solved

    return {
        "total_solved": total_problems_solved,
        "session_solved": total_session_solved,
        "total_practice_minutes": round(total_time_seconds / 60),
        "difficulty_breakdown": difficulty_counts,
        "topic_breakdown": topic_distribution,
        "synced_accounts": synced_accounts,
        "recent_sessions": _CODING_SESSIONS[-5:]
    }
