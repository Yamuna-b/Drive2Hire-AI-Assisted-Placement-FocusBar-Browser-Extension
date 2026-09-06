from fastapi import APIRouter
from pydantic import BaseModel, Field

from backend.services.platform_sync import sync_handles

router = APIRouter()


class SyncRequest(BaseModel):
    leetcode: str = ""
    gfg: str = ""
    codeforces: str = ""
    hackerrank: str = ""


@router.get("/test")
async def test():
    return {"msg": "coding router works"}


@router.post("/sync")
async def coding_sync(request: SyncRequest):
    return await sync_handles(request.model_dump())
