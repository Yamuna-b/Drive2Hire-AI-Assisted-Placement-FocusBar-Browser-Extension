# Placement FocusBar

Chrome side-panel extension + FastAPI backend that helps engineering students prepare for placements.

## Current status — working local MVP

- **Visible-page extraction** works on common job pages and rejects pages that do not look like job postings
- Intelligently extracts job title, company, description from unknown websites
- Extended skills database with 200+ domain-specific skills (Siemens eMeter, EnergyIP, MDMS, SAP, Oracle, etc.)
- Dynamic skill extraction for domain-specific terms not in predefined database
- Auto-detects job pages and extracts content automatically with MutationObserver

## Implemented product flow

- Sign in locally or with Google OAuth verification
- Consent-gated live job analysis with readiness score and evidence findings
- Resume upload/paste, Resume-JD Match Score, missing sections, and suggestions
- Public coding profile sync with source and retrieval time
- Saved job/application snapshots stored in extension storage
- Dark side-panel UI with honest loading, empty, and unavailable states

## Supported extraction approach

- Job-page DOM parsing for common LinkedIn, Naukri, Indeed, Glassdoor, and career-page layouts
- `POST /job/analyse` — rule-based mandatory vs nice-to-have skill extraction
- Detects and extracts skills from complete job description text
- Job tab shows snapshot, skills, and covered / weak / missing match vs user profile

## Phase 1 status (complete)

- Manifest V3 extension with Job / Company / Coding / Settings tabs
- Side panel opens when you click the extension icon
- FastAPI backend with `/health`, `/docs`, all routers registered
- PostgreSQL models available (tables auto-created on startup when DB is reachable)

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

## What is still missing

- Backend sessions/JWT and user-scoped PostgreSQL persistence
- Project evidence management and editable detected requirements
- Reliable topic-level coding evidence, beginning with LeetCode
- Live, sourced company facts beyond the current job page
- Production hosting, Chrome Web Store publishing, and Firefox packaging

### Test Phase 4 (Universal Extraction)

1. Start backend: `.\scripts\start-backend.ps1`
2. Reload extension at `chrome://extensions`
3. Open a supported job listing page:
   - LinkedIn Jobs (known site)
   - Naukri (known site)
   - Indeed (known site)
   - Accenture careers page (generic site)
4. Click the extension icon → **Job** tab
5. Job data should auto-extract (or click "Analyze current job page")
6. You should see job title, skills, and your match breakdown
7. Click "Refine Skills Q&A" to answer questions about gap skills

### Testing Universal Extraction with Accenture Example

For the Accenture Application Developer role, the extension should now:
- Extract from Accenture's careers page (any website)
- Identify "Siemens eMeter" as required skill (from expanded skills.json)
- Extract other domain-specific terms like "EnergyIP MDMS", "Configuration MDMS"
- Show accurate mandatory skills (not generic Java/Spring Boot)
- Compare against your profile and show gaps
- Allow Q&A refinement for experience with Siemens eMeter

### Test Phase 3 (Q&A Refinement)

1. Complete Phase 4 testing first
2. On any analyzed job page, click the **Refine Skills Q&A** button
3. A modal should appear with questions about skills that have experience gaps
4. Answer questions about your experience duration and project notes
5. Click "Save & Re‑analyze" to update your profile
6. Your skill match should be recalculated based on responses

**Example:** For Accenture job, if you don't have Siemens eMeter experience, 
the Q&A will ask about your background and let you note if you're willing to learn it.

## Skills Database

The backend includes 200+ predefined skills across categories:
- **Languages**: Python, Java, C++, Go, Rust, PHP, Scala, R, MATLAB
- **Frameworks**: Spring Boot, FastAPI, Django, Flask, Express, Angular, React, Vue
- **Databases**: SQL, MongoDB, Redis, PostgreSQL, Cassandra, HBase, Snowflake
- **Enterprise**: SAP, Salesforce, Oracle, .NET, CICS, DB2, Teradata, Netezza
- **Domain-Specific**: Siemens eMeter, EnergyIP, MDMS, AMI, Informatica, Talend
- **Cloud**: AWS, Azure, GCP, Docker, Kubernetes, Terraform, CloudFormation
- **DevOps**: CI/CD, Jenkins, GitLab, GitHub, SonarQube, Ansible, Chef
- **Data**: Spark, Hadoop, Kafka, ETL, Tableau, Power BI, Looker
- **AI/ML**: TensorFlow, PyTorch, scikit-learn, Pandas, NumPy, NLP, CV
- **Security**: OAuth, JWT, SSL/TLS, Kerberos, LDAP, Active Directory
- **Professional**: Agile, Scrum, Kanban, DevOps, SRE, TDD, Design Patterns

Unknown skills found in the job description are automatically extracted as "domain-specific" skills.

## Default User Skills

Default user skills are stored in extension local storage (editable via Q&A refinement):
- Python (strong, 2+ years)
- JavaScript (moderate, 1 year)
- SQL (moderate, 1 year)
- Git (strong, 2+ years)
- React (weak)
- DSA (moderate)
- REST (moderate)

## Docs

- [Architecture](docs/architecture.md)
- [Data models](docs/data-models.md)
- [API endpoints](docs/api-endpoints.md)
