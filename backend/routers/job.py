from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from backend.services.jd_parser import parse_jd
from backend.db.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

class JobAnalyseRequest(BaseModel):
    title: str
    company: str
    jd: str

@router.post("/analyse")
async def analyse_job(request: JobAnalyseRequest):
    # Simple rule‑based parsing – extract keywords from JD
    result = parse_jd(request.jd)
    # For now we just return the parsed result
    return {"title": request.title, "company": request.company, "keywords": result}
