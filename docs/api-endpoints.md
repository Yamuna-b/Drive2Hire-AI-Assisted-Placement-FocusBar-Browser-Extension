# API Endpoints

Base URL: `http://127.0.0.1:8000`

Interactive API documentation: `http://127.0.0.1:8000/docs`

## Runtime

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | Service identity and docs link |
| GET | `/health` | API and PostgreSQL status |
| POST | `/auth/google` | Verify a Google access token |
| GET | `/auth/health` | OAuth configuration status |

## Live job and readiness analysis

| Method | Path | Purpose |
|---|---|---|
| POST | `/job/analyse` | Parse current job text and return requirements, readiness, evidence, priorities, source, and timestamp |

The request may include `title`, `company`, `jd`, `location`, `work_mode`, `page_url`, `user_skills`, `resume_text`, and `coding_stats`. The readiness result is calculated from those values only.

## Resume

| Method | Path | Purpose |
|---|---|---|
| POST | `/user/resume/upload` | Extract text from PDF, DOCX, or TXT |
| POST | `/user/resume/check` | Return Resume-JD Match Score, keyword gaps, formatting flags, missing sections, and suggestions |

## Company

| Method | Path | Purpose |
|---|---|---|
| POST | `/company/from-page` | Return company and technology facts found in the submitted page text |
| POST | `/company/analyze-realtime` | Alias for current-page company analysis |

Company responses intentionally do not claim salary, leadership, or interview facts without a verified source.

## Coding

| Method | Path | Purpose |
|---|---|---|
| POST | `/coding/sync` | Fetch available public profile fields for supplied usernames |

The sync returns an explicit error for unavailable, private, invalid, blocked, or unreadable profiles. It does not convert failures into zero counts.

## Q&A, applications, and roadmap

The repository also exposes Q&A, application, coding-session, and gap-analysis routes. These are useful local APIs, but database-backed persistence requires `DATABASE_URL`. `/gap-analysis/job-match/{user_id}` does not return a fabricated score; use `/job/analyse` with the live job description instead.

## Error policy

The API returns an error or an unavailable status when the page, resume, profile, or external source cannot be verified. Clients should show that state to the user rather than substituting demo data.
