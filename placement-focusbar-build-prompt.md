# Build Prompt: Placement FocusBar

Copy everything below into Claude Code (or any AI coding assistant) to scaffold and build the project.

---

## PROMPT START

You are building a project called **"Placement FocusBar"** — a Chrome browser sidebar extension + backend + web app that helps engineering students prepare for placements by giving job-level insights, company-level insights, ATS-aware resume guidance, and coding-practice tracking mapped to job skills.

### Hard constraints (do not deviate)

1. **Language: JavaScript only. Do NOT use TypeScript anywhere** — not in the extension, not in the backend (if a JS backend module is used), not in the web app. No `.ts`/`.tsx` files, no `tsconfig.json`, no type-only syntax.
2. **If any third-party API key, account credential, or paid service is required at any point (e.g. LinkedIn scraping, salary data APIs, AI model API, coding-platform APIs, hosting/deployment tokens), STOP and ask me for it or ask me how I want to source that data before writing code that depends on it.** Never invent placeholder keys and silently proceed as if they exist — always surface the requirement to me first.
3. Build everything so it **runs and is testable fully for free/local** during development (no paid services required to reach a working MVP).
4. Keep the actual extension UI **minimal and text-first** ("focus-bar" philosophy) — no heavy dashboards, no charting libraries, no visual clutter. Checklists, labels, plain text.
5. Start with **rule-based / deterministic logic everywhere it's possible** (keyword matching, regex, DOM parsing, heuristics). Only wire in an AI model call where it's explicitly optional/enhanced — and if you add that, ask me first whether I want to enable it and which model/API to use.

### Tech stack

- **Extension:** Chrome Manifest V3, plain JavaScript + HTML + CSS (no React unless I ask for it later). Uses `side_panel` for the FocusBar UI, content scripts for DOM reading, background service worker for API calls/session timers.
- **Backend:** Python + FastAPI (preferred) or Django REST — your choice, but tell me which and why. Backend serves JSON REST APIs consumed by the extension and (optionally) a web app.
- **Web app (optional, for profile/settings/detailed views):** Plain JavaScript + HTML/CSS, or React **with JavaScript (.jsx, not .tsx)** if component state gets complex — no TypeScript either way.
- **Database:** PostgreSQL (preferred) — assume local Postgres for dev; mention free-tier hosted options (Render/Railway/Supabase) as a later step, don't wire them in yet.
- **Deployment:** Local-first. Note free deployment paths (Render/Railway for backend, GitHub Pages/Vercel/Netlify for web app, $5 one-time Chrome Web Store dev fee for publishing) as documentation only — don't actually deploy anything without asking me.

### Project structure to scaffold

```
placement-focusbar/
├── extension/
│   ├── manifest.json
│   ├── side_panel/
│   │   ├── focusbar.html
│   │   ├── focusbar.js
│   │   └── focusbar.css
│   ├── content-scripts/
│   │   ├── job-page-parser.js       // reads job title/company/JD text from LinkedIn/Naukri/etc
│   │   └── coding-page-parser.js    // reads problem title/tags/difficulty from LeetCode/GFG/Codeforces
│   ├── background/
│   │   └── service-worker.js        // routes messages, calls backend API, manages session timers
│   ├── icons/
│   └── shared/
│       └── api-client.js            // fetch wrapper for backend calls
│
├── backend/
│   ├── main.py                      // FastAPI app entrypoint
│   ├── requirements.txt
│   ├── config.py                    // env vars, no hardcoded secrets
│   ├── models/                      // DB models: User, Skill, Resume, Job, Company, CodingSession, CodingAccountSync, JobOutcome
│   ├── routers/
│   │   ├── job.py                   // POST /job/analyse, POST /job/outcome
│   │   ├── resume.py                // POST /user/resume, ATS checks
│   │   ├── company.py               // GET /company/{company_name}
│   │   ├── coding.py                // POST /coding/session, GET /coding/summary, POST /coding/account-sync
│   │   └── qa.py                    // Q&A skill refinement endpoints
│   ├── services/
│   │   ├── jd_parser.py             // rule-based skill/keyword extraction from JD text
│   │   ├── ats_checker.py           // rule-based ATS/resume format + keyword checks
│   │   ├── skill_matcher.py         // compares user skills vs JD requirements
│   │   └── coding_tracker.py        // aggregates session + account-sync coding stats
│   └── db/
│       ├── database.py              // DB connection/session setup
│       └── migrations/
│
├── webapp/ (optional, build after extension+backend work)
│   ├── index.html
│   ├── src/
│   │   ├── App.jsx
│   │   ├── pages/ (Profile.jsx, ResumeUpload.jsx, Settings.jsx)
│   │   └── components/
│   └── package.json
│
├── docs/
│   ├── api-endpoints.md
│   ├── data-models.md
│   └── architecture.md
│
└── README.md
```

### Features to implement, in this order

**Phase 1 — Extension skeleton + local backend**
1. Manifest V3 extension that opens a side panel on any page, with a placeholder FocusBar UI (Job tab / Company tab / Coding tab as simple text sections).
2. FastAPI backend with a health-check endpoint, connected to local Postgres, with the models listed above stubbed out.

**Phase 2 — Job-level view**
3. Content script that extracts job title, company name, and JD text from the current page's DOM (support LinkedIn and Naukri page structures to start; make the selector logic easy to extend to other job boards).
4. `POST /job/analyse`: rule-based keyword matching against a configurable skills list, splitting "mandatory" vs "nice-to-have" based on JD section headings (regex/heading detection).
5. Sidebar renders: job snapshot, mandatory/nice-to-have skills, and a simple "your match" comparison (covered / weak / missing) against a stored user skill profile.

**Phase 3 — Q&A skill refinement**
6. When a JD skill requirement includes an experience duration (e.g. "2+ years Docker") and the user's stored profile has the skill but no duration, trigger a short Q&A flow in the sidebar (yes/no + multiple-choice duration + short free-text project description).
7. Store answers back into the user's structured skill profile and re-run the match.

**Phase 4 — ATS / resume check**
8. `POST /user/resume` to store resume text/structured data.
9. Rule-based ATS checker: flags missing standard section headings, tables/images (bad for ATS parsing), and missing JD keywords. Returns plain-text style output ("ATS-safe: Yes/No", "Missing keywords: ...").

**Phase 5 — Company-level view**
10. `GET /company/{company_name}`: rule-based extraction from whatever source of company data I approve (ask me before deciding on a source — company website scraping, a specific API, or manual/static data entry for MVP).
11. Sidebar Company tab: type (product/service), industry, locations, typical roles, tech stack, salary bands (only if I've confirmed a data source), leadership info if public.

**Phase 6 — Coding practice tracking**
12. Content script for LeetCode/GFG/Codeforces problem pages: extract problem title, tags/topics, difficulty; start/stop a session timer.
13. `POST /coding/session` to log each session.
14. `POST /coding/account-sync`: background sync of a user-provided public profile handle — **ask me first** about which platform APIs/scraping approach is allowed per platform's ToS before implementing this.
15. `GET /coding/summary`: aggregate topic-wise/difficulty-wise stats from both session logs and account sync.

**Phase 7 — Job-to-skill-gap mapping**
16. For a given job, combine JD's DSA/skill requirements with the user's coding topic stats and skill profile to produce a short gap summary and a simple suggested prep list (e.g. "Trees: weak, Graphs: missing — practice 3 Tree + 3 Graph problems this week").

**Phase 8 — Outcome tracking**
17. `POST /job/outcome` to log applied/rejected/shortlisted status per job, with an optional reason field, so future job matches can reference past outcomes.

### Data models needed (design these first, show me the schema before writing full CRUD)

- User (profile, auth — keep auth minimal/local for MVP, ask me before adding OAuth/third-party login)
- Skill (name, category)
- UserSkill (user_id, skill_id, duration_bucket, project_notes)
- Resume (user_id, raw_text, structured_sections, ats_flags, version)
- Job (title, company_name, location, experience_range, jd_text, mandatory_skills, nice_to_have_skills)
- Company (name, type, industry, locations, roles, tech_stack, salary_bands, leadership)
- CodingSession (user_id, platform, problem_id, topics, difficulty, start_time, end_time)
- CodingAccountSync (user_id, platform, handle, total_solved, topic_breakdown, last_synced_at)
- JobOutcome (user_id, job_id, status, reason, applied_at)

### What I want from you right now

1. Confirm the exact folder structure above (adjust only if there's a clear technical reason, and tell me why).
2. Scaffold Phase 1 completely: extension skeleton (manifest.json + side panel placeholder) and backend skeleton (FastAPI app + Postgres connection + empty model files), all in plain JavaScript/Python, no TypeScript anywhere.
3. Before touching anything that needs an external API, scraping target, or paid service (company data sources, coding-platform sync, any AI model calls, hosting/deployment), **stop and ask me** how I want to handle it.
4. After each phase, give me a short summary of what was built and how to run/test it locally before moving to the next phase.

## PROMPT END
