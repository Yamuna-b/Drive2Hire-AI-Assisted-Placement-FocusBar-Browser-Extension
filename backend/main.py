from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from backend.db.database import engine
from backend.db.init_db import init_db
from backend.routers import (
    job, resume, company, coding, qa, 
    coding_session, gap_analysis, application_tracking, github
)

app = FastAPI(title="Placement FocusBar Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    app.state.db_ready = await init_db()


@app.get("/health")
async def health_check():
    if not engine:
        return {"status": "ok", "database": "not_configured"}

    db_status = "disconnected"
    if getattr(app.state, "db_ready", False):
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            db_status = "connected"
        except Exception:
            db_status = "error"
    return {"status": "ok", "database": db_status}


@app.get("/")
async def root():
    return {"message": "Placement FocusBar Backend", "docs": "/docs"}


# Phase 1-2: Job parsing and basic features
app.include_router(job.router, prefix="/job", tags=["job"])
app.include_router(resume.router, prefix="/user", tags=["resume"])

# Phase 3: Q&A and skill refinement
app.include_router(qa.router, prefix="/qa", tags=["qa"])

# Phase 5: Company insights
app.include_router(company.router, prefix="/company", tags=["company"])

# Phase 6: Coding session tracker
app.include_router(coding.router, prefix="/coding", tags=["coding"])
app.include_router(coding_session.router, prefix="/coding-session", tags=["coding-session"])

# Phase 7: Gap analysis and learning roadmap
app.include_router(gap_analysis.router, prefix="/gap-analysis", tags=["gap-analysis"])

# Phase 8: Application tracking
app.include_router(application_tracking.router, prefix="/applications", tags=["applications"])

# GitHub API integration
app.include_router(github.router, prefix="/github", tags=["github"])
