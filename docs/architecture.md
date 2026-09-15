# Drive2Hire Architecture

## Components

| Layer | Tech | Role |
|-------|------|------|
| Extension UI | HTML/CSS/JS | Side panel FocusBar (Job / Company / Coding tabs) |
| Content scripts | Plain JS | Read job/coding pages (Phase 2+) |
| Service worker | Plain JS | Side panel behavior, message routing, API calls |
| Backend | FastAPI (Python) | REST JSON APIs |
| Database | PostgreSQL via SQLAlchemy async | Durable users, skills, Q&A, companies, sessions, applications |

## Runtime Architecture

```mermaid
flowchart LR
        Browser[Job board or coding page]
        Parser[Content extraction scripts]
        Worker[MV3 service worker]
        Panel[Side panel UI]
        API[FastAPI REST API]
        DB[(PostgreSQL)]
        External[Google OAuth and public coding APIs]

        Browser --> Parser
        Parser --> Worker
        Panel <--> Worker
        Worker -->|analyse, sync, auth| API
        API <--> DB
        API --> External
        External --> API
        API --> Worker
        Worker --> Panel
```

## Authentication and storage boundary

The current sign-in experience is local-first. Google OAuth verifies the account and the extension stores the active profile in `chrome.storage.local`, but the backend does not yet issue a session or associate API writes with a user ID. Job analysis and UI preferences therefore work without PostgreSQL; persistent multi-device data does not.

## Feature flow

```mermaid
sequenceDiagram
        participant U as User
        participant E as Extension
        participant A as FastAPI
        participant D as PostgreSQL

        U->>E: Open job page and analyze
        E->>E: Extract title, company, JD
        E->>A: POST /job/analyse + profile skills
        A-->>E: Skills, match, experience signals
        E-->>U: Render live Job tab
        U->>E: Upload resume or run ATS check
        E->>A: POST /user/resume/upload or /check
        A-->>E: Parsed text or score and gaps
        U->>E: Save application / Q&A / coding sync
        E->>A: Feature API request
        A->>D: Persist when DATABASE_URL is configured
        D-->>A: Stored result
        A-->>E: Updated result
```

The extension refreshes backend health every 15 seconds and updates its panel when Chrome storage changes. The backend currently runs in a useful degraded mode without PostgreSQL, while database-backed features need `DATABASE_URL` and a reachable PostgreSQL instance.

## Current gaps

- Backend authentication is verification-only; there is no issued session/JWT or user-scoped persistence.
- Most extension actions are local storage actions, so data does not follow a user to another browser or device.
- Coding sync is public-profile fetching, not authenticated platform integration; some platform adapters remain limited.
- Company salary and leadership data are not sourced yet.
- The extension is load-unpacked only. Cross-browser packaging and store distribution are not configured.

## Local-first

No paid services required for MVP development. Deployment options (Render, Railway, Chrome Web Store) are documented for later phases only.
