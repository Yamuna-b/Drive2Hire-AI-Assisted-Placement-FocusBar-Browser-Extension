# Data models — Phase 1 stubs

All models live in `backend/models/`. Tables are created via SQLAlchemy `create_all` on startup when PostgreSQL is available.

| Model | Table | Purpose |
|-------|-------|---------|
| User | users | Profile (minimal local auth later) |
| Skill | skills | Canonical skill names + category |
| UserSkill | user_skills | Per-user skill level, duration, project notes |
| Resume | resumes | Raw text, structured sections, ATS flags |
| Job | jobs | Parsed JD, mandatory/nice-to-have skills |
| Company | companies | Company profile fields |
| CodingSession | coding_sessions | Per-problem practice sessions |
| CodingAccountSync | coding_account_syncs | Platform handle sync stats |
| JobOutcome | job_outcomes | Applied / rejected / shortlisted tracking |

Full CRUD and migrations (Alembic) arrive in later phases.
