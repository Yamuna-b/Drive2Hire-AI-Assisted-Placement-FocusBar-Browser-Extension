# API endpoints

Base URL (local): `http://127.0.0.1:8000`

Interactive docs: http://127.0.0.1:8000/docs

## Phase 2 (live)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/job/analyse` | Parse JD → mandatory/nice-to-have skills + user match |

Request body:

```json
{
  "title": "Software Engineer",
  "company": "Example Corp",
  "jd": "Required: Python, Docker...",
  "user_skills": [{ "name": "Python", "level": "strong" }]
}
```

Response includes `mandatory_skills`, `nice_to_have_skills`, and `match` (`covered` / `weak` / `missing`).

## Phase 1 (live)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | API welcome |
| GET | `/health` | API + database status |
| GET | `/user/test` | Resume router stub |
| GET | `/company/test` | Company router stub |
| GET | `/coding/test` | Coding router stub |
| GET | `/qa/health` | Q&A router stub |

## Phase 2+ (planned)

| Method | Path | Phase |
|--------|------|-------|
| POST | `/job/analyse` | 2 |
| POST | `/job/outcome` | 8 |
| POST | `/user/resume` | 4 |
| GET | `/company/{company_name}` | 5 |
| POST | `/coding/session` | 6 |
| GET | `/coding/summary` | 6 |
| POST | `/coding/account-sync` | 6 |
