from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os

import httpx

router = APIRouter()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID") or (
    "758501915824-n03vtotgp025jc2gmn7hnsg5gh6lik0k.apps.googleusercontent.com"
)


class GoogleTokenRequest(BaseModel):
    access_token: str


@router.get("/health")
async def auth_health():
    return {
        "google_oauth": bool(GOOGLE_CLIENT_ID),
        "msg": "Paste GOOGLE_CLIENT_ID in .env and in the extension Settings to enable Google sign-in.",
    }


@router.post("/google")
async def google_login(request: GoogleTokenRequest):
    """Exchange a Google access token for a local session profile (no invented keys)."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        res = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {request.access_token}"},
        )
    if res.status_code != 200:
        raise HTTPException(status_code=401, detail="Google token was rejected. Recreate OAuth client ID.")
    info = res.json()
    return {
        "ok": True,
        "user": {
            "name": info.get("name") or "",
            "email": info.get("email") or "",
            "picture": info.get("picture") or "",
            "google_id": info.get("sub") or "",
        },
    }
