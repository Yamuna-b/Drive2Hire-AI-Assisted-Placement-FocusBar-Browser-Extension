# Architecture — Phase 1

## Components

| Layer | Tech | Role |
|-------|------|------|
| Extension UI | HTML/CSS/JS | Side panel FocusBar (Job / Company / Coding tabs) |
| Content scripts | Plain JS | Read job/coding pages (Phase 2+) |
| Service worker | Plain JS | Side panel behavior, message routing, API calls |
| Backend | FastAPI (Python) | REST JSON APIs |
| Database | PostgreSQL | User profile, jobs, skills, coding sessions |

## Data flow (Phase 2+)

```
Job board page → content script → service worker → FastAPI → PostgreSQL
                                      ↓
                              side panel UI update
```

Phase 1 only verifies: extension loads, side panel opens, backend `/health` responds.

## Local-first

No paid services required for MVP development. Deployment options (Render, Railway, Chrome Web Store) are documented for later phases only.
