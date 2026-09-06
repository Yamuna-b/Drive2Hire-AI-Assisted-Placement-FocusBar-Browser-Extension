"""Fetch public coding-platform stats. No API keys. Returns errors instead of invented numbers."""
import re
from typing import Any

import httpx

HEADERS = {
    "User-Agent": "Drive2Hire/0.3 (placement prep; local student tool)",
    "Accept": "application/json,text/html",
}


async def fetch_leetcode(username: str) -> dict[str, Any]:
    query = """
    query getUserProfile($username: String!) {
      matchedUser(username: $username) {
        username
        submitStats: submitStatsGlobal {
          acSubmissionNum { difficulty count }
        }
        profile { ranking reputation }
      }
    }
    """
    async with httpx.AsyncClient(timeout=20.0, headers=HEADERS) as client:
        res = await client.post(
            "https://leetcode.com/graphql",
            json={"query": query, "variables": {"username": username}},
        )
    if res.status_code != 200:
        return {"ok": False, "platform": "leetcode", "error": f"HTTP {res.status_code}"}
    data = res.json()
    user = (data.get("data") or {}).get("matchedUser")
    if not user:
        return {"ok": False, "platform": "leetcode", "error": "Handle not found or profile is private."}
    counts = {row["difficulty"].lower(): row["count"] for row in user.get("submitStats", {}).get("acSubmissionNum", [])}
    return {
        "ok": True,
        "platform": "leetcode",
        "handle": username,
        "total_solved": counts.get("all", 0),
        "easy": counts.get("easy", 0),
        "medium": counts.get("medium", 0),
        "hard": counts.get("hard", 0),
        "ranking": (user.get("profile") or {}).get("ranking"),
        "source": "leetcode.com/graphql (public)",
    }


async def fetch_codeforces(handle: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=20.0, headers=HEADERS) as client:
        info = await client.get(f"https://codeforces.com/api/user.info?handles={handle}")
        status = await client.get(
            f"https://codeforces.com/api/user.status?handle={handle}&from=1&count=10000"
        )
    if info.status_code != 200:
        return {"ok": False, "platform": "codeforces", "error": f"HTTP {info.status_code}"}
    body = info.json()
    if body.get("status") != "OK" or not body.get("result"):
        return {"ok": False, "platform": "codeforces", "error": body.get("comment") or "Handle not found."}
    user = body["result"][0]
    solved = set()
    if status.status_code == 200:
        st = status.json()
        if st.get("status") == "OK":
            for sub in st.get("result") or []:
                if sub.get("verdict") == "OK":
                    prob = sub.get("problem") or {}
                    solved.add(f"{prob.get('contestId')}-{prob.get('index')}")
    return {
        "ok": True,
        "platform": "codeforces",
        "handle": handle,
        "rating": user.get("rating"),
        "max_rating": user.get("maxRating"),
        "rank": user.get("rank"),
        "total_solved": len(solved),
        "source": "codeforces.com/api (public)",
    }


async def fetch_gfg(username: str) -> dict[str, Any]:
    urls = [
        f"https://www.geeksforgeeks.org/user/{username}/",
        f"https://auth.geeksforgeeks.org/user/{username}/",
    ]
    html = ""
    async with httpx.AsyncClient(timeout=20.0, headers=HEADERS, follow_redirects=True) as client:
        for url in urls:
            res = await client.get(url)
            if res.status_code == 200 and len(res.text) > 200:
                html = res.text
                break
    if not html:
        return {"ok": False, "platform": "gfg", "error": "Could not load public GFG profile. Check the username."}

    def first_int(patterns):
        for pattern in patterns:
            match = re.search(pattern, html, re.I)
            if match:
                digits = re.sub(r"[^\d]", "", match.group(1))
                if digits:
                    return int(digits)
        return None

    coding_score = first_int([r"coding[\s_-]*score[^0-9]{0,40}(\d[\d,]*)", r'"score"\s*:\s*(\d+)'])
    problems = first_int(
        [
            r"problem[s]?\s*solved[^0-9]{0,40}(\d[\d,]*)",
            r'"total_problems_solved"\s*:\s*(\d+)',
            r"Institute Rank.*?(\d+)",
        ]
    )
    if coding_score is None and problems is None:
        return {
            "ok": False,
            "platform": "gfg",
            "error": "Profile loaded but stats were not readable (layout change or private).",
        }
    return {
        "ok": True,
        "platform": "gfg",
        "handle": username,
        "coding_score": coding_score,
        "total_solved": problems,
        "source": "public GFG profile page",
    }


async def fetch_hackerrank(username: str) -> dict[str, Any]:
    url = f"https://www.hackerrank.com/rest/hackers/{username}/profile"
    async with httpx.AsyncClient(timeout=20.0, headers=HEADERS) as client:
        res = await client.get(url)
    if res.status_code != 200:
        return {"ok": False, "platform": "hackerrank", "error": f"HTTP {res.status_code}"}
    model = (res.json() or {}).get("model") or {}
    if not model:
        return {"ok": False, "platform": "hackerrank", "error": "Handle not found or profile is private."}
    return {
        "ok": True,
        "platform": "hackerrank",
        "handle": username,
        "name": model.get("name"),
        "country": model.get("country"),
        "followers": model.get("followers_count"),
        "source": "hackerrank.com public REST profile",
    }


async def sync_handles(handles: dict) -> dict:
    results = {}
    if handles.get("leetcode"):
        results["leetcode"] = await fetch_leetcode(handles["leetcode"].strip())
    if handles.get("gfg"):
        results["gfg"] = await fetch_gfg(handles["gfg"].strip())
    if handles.get("codeforces"):
        results["codeforces"] = await fetch_codeforces(handles["codeforces"].strip())
    if handles.get("hackerrank"):
        results["hackerrank"] = await fetch_hackerrank(handles["hackerrank"].strip())
    if not results:
        return {"ok": False, "error": "Save at least one public username in Settings."}
    return {"ok": True, "stats": results}
