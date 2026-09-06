from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from io import BytesIO

from backend.services.ats_checker import check_ats

router = APIRouter()


class SkillItem(BaseModel):
    name: str
    duration: Optional[str] = None


class ResumeCheckRequest(BaseModel):
    resume_text: str
    jd_text: Optional[str] = ""
    mandatory_skills: Optional[List[SkillItem]] = []
    nice_to_have_skills: Optional[List[SkillItem]] = []


def _text_from_upload(filename: str, data: bytes) -> str:
    name = (filename or "").lower()
    if name.endswith(".txt"):
        return data.decode("utf-8", errors="ignore")
    if name.endswith(".pdf"):
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise HTTPException(status_code=500, detail="pypdf is not installed. pip install pypdf") from exc
        reader = PdfReader(BytesIO(data))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages)
    if name.endswith(".docx"):
        try:
            import zipfile
            import xml.etree.ElementTree as ET
        except ImportError as exc:
            raise HTTPException(status_code=400, detail="Cannot read this file type") from exc
        with zipfile.ZipFile(BytesIO(data)) as zf:
            xml_bytes = zf.read("word/document.xml")
        root = ET.fromstring(xml_bytes)
        texts = [node.text or "" for node in root.iter() if node.text]
        return "\n".join(texts)
    raise HTTPException(status_code=400, detail="Use PDF, DOCX, or TXT.")


@router.post("/resume/upload")
async def upload_resume(file: UploadFile = File(...)):
    data = await file.read()
    text = _text_from_upload(file.filename or "", data).strip()
    if not text:
        raise HTTPException(status_code=400, detail="No text could be read from that file.")
    return {"ok": True, "filename": file.filename, "resume_text": text, "chars": len(text)}


@router.post("/resume/check")
async def check_resume(request: ResumeCheckRequest):
    result = check_ats(
        resume_text=request.resume_text,
        jd_text=request.jd_text or "",
        mandatory_skills=[s.model_dump() for s in (request.mandatory_skills or [])],
        nice_to_have_skills=[s.model_dump() for s in (request.nice_to_have_skills or [])],
    )
    return result
