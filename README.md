# Placement FocusBar

Chrome side-panel extension + FastAPI backend that helps engineering students prepare for placements.

## Phase 2 status (complete)

- Job-page DOM parsing for LinkedIn and Naukri (extensible selector map)
- `POST /job/analyse` — rule-based mandatory vs nice-to-have skill extraction
- Job tab shows snapshot, skills, and covered / weak / missing match vs default user profile

## Phase 1 status (complete)

- Manifest V3 extension with Job / Company / Coding tabs (text-first placeholder UI)
- Side panel opens when you click the extension icon
- FastAPI backend with `/health`, `/docs`, stub routers
- PostgreSQL models stubbed (tables auto-created on startup when DB is reachable)

## Project layout

```
Drive2Hire/
├── extension/          # Chrome extension (plain JS + HTML + CSS)
├── backend/            # FastAPI + SQLAlchemy + PostgreSQL
├── docs/               # Architecture and API notes
└── scripts/            # Local run helpers
```

## Prerequisites

- Python 3.11+
- PostgreSQL (local) — optional for Phase 1 UI; required for DB features
- Google Chrome

## 1. Backend setup

```powershell
cd "C:\Users\yamun\Desktop\Placement Projects\Drive2Hire"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
copy .env.example .env
```

Create the database (adjust user/password if needed):

```sql
CREATE DATABASE placement_focusbar;
```

Start the API (from project root):

```powershell
.\scripts\start-backend.ps1
```

Verify:

- http://127.0.0.1:8000/ → `{"message":"Placement FocusBar Backend","docs":"/docs"}`
- http://127.0.0.1:8000/health → `{"status":"ok","database":"not_configured"}` (no `.env`) or `"connected"` when Postgres is set up

### PostgreSQL (optional for now)

Phases 1–2 **do not require** a database. If you see `password authentication failed for user "yamun"`, Postgres is running but no credentials are configured.

**Quick fix — skip DB for now:** do nothing. Restart the backend; health will show `"database":"not_configured"` and job analysis still works.

**To connect Postgres later:**

1. `copy .env.example .env`
2. Edit `.env` — set your postgres user/password (often user `postgres`, password from install)
3. Create DB in psql or pgAdmin: `CREATE DATABASE placement_focusbar;`
4. Restart backend

Example `.env`:

```
DATABASE_URL=postgresql+asyncpg://postgres:yourpassword@localhost:5432/placement_focusbar
```

## 2. Load the Chrome extension

1. Open `chrome://extensions`
2. Enable **Developer mode**
3. Click **Load unpacked**
4. Select the `extension/` folder (not the repo root)
5. Pin **Placement FocusBar** in the toolbar
6. Click the icon on any page → side panel opens

The footer in the side panel shows backend connectivity.

After code changes: click **Reload** on `chrome://extensions`, then reopen the side panel.

## What's next — Phase 3

Phase 3 adds Q&A skill refinement when JD mentions experience duration.

### Test Phase 2

1. Start backend: `.\scripts\start-backend.ps1`
2. Reload extension at `chrome://extensions`
3. Open a **LinkedIn** or **Naukri** job listing page
4. Click the extension icon → **Job** tab
5. Click **Analyze current job page** (or wait for auto-extract on page load)
6. You should see job title, skills, and your match breakdown

Default user skills are stored in extension local storage (editable in Phase 3+).

## Docs

- [Architecture](docs/architecture.md)
- [Data models](docs/data-models.md)
- [API endpoints](docs/api-endpoints.md)
