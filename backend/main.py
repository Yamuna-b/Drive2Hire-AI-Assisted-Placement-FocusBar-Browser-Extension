from fastapi import FastAPI
from backend.routers import job, resume, company, coding

app = FastAPI(title="Placement FocusBar Backend")

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/")
async def root():
    return {"message": "Placement FocusBar Backend"}

# Include routers (currently empty)
app.include_router(job.router, prefix="/job", tags=["job"])
app.include_router(resume.router, prefix="/user", tags=["resume"])
app.include_router(company.router, prefix="/company", tags=["company"])
app.include_router(coding.router, prefix="/coding", tags=["coding"])
# app.include_router(qa.router, prefix="/qa", tags=["qa"])  # QA router not implemented
