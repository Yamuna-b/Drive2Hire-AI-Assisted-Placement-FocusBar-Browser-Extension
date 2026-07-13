from fastapi import APIRouter

router = APIRouter()

# Placeholder endpoint – you can extend later
@router.get("/test")
async def test():
    return {"msg": "resume router works"}
