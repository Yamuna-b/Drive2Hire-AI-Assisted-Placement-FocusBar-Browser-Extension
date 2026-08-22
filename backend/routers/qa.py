from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def qa_health():
    return {"msg": "qa router stub — Phase 3 will add skill Q&A endpoints"}
