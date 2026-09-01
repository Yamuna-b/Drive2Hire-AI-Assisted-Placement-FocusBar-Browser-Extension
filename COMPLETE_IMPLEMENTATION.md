# Drive2Hire Placement Assistant - Complete Implementation Guide

## Overview

Drive2Hire is a Chrome extension that helps engineering students prepare for tech placements by:
1. **Extracting job requirements** from any website
2. **Matching user skills** against job requirements
3. **Providing personalized learning roadmaps**
4. **Tracking coding practice** across platforms
5. **Managing job applications** with outcome tracking
6. **Offering company insights** from aggregated data

---

## Architecture

### Tech Stack
- **Frontend**: HTML/CSS/JavaScript (Chrome Extension)
- **Backend**: FastAPI (Python)
- **Database**: SQLite/PostgreSQL (via SQLAlchemy ORM)
- **Content Parsing**: Universal DOM parsing + LeetCode/GFG/Codeforces APIs

### Folder Structure
```
Drive2Hire/
├── extension/                    # Chrome extension
│   ├── manifest.json            # Extension configuration
│   ├── side_panel/              # UI components
│   │   ├── focusbar.html
│   │   └── focusbar.js
│   ├── content-scripts/         # Page content injection
│   │   └── universal-parser.js  # Generic DOM extraction
│   └── background/
│       └── service-worker.js
│
├── backend/                     # FastAPI server
│   ├── main.py                 # App entry point
│   ├── routers/                # API endpoints
│   │   ├── job.py              # Phase 1-2: Job parsing
│   │   ├── qa.py               # Phase 3: Q&A with DB persistence
│   │   ├── company.py          # Phase 5: Company insights
│   │   ├── coding_session.py   # Phase 6: Coding tracker
│   │   ├── gap_analysis.py     # Phase 7: Learning roadmap
│   │   └── application_tracking.py # Phase 8: App tracking
│   │
│   ├── models/                 # SQLAlchemy ORM models
│   │   ├── user.py
│   │   ├── user_skill.py
│   │   ├── company.py          # Company aggregate data
│   │   ├── coding_session.py   # Coding practice tracking
│   │   ├── qa_response.py      # Q&A responses
│   │   └── application.py      # Job applications
│   │
│   ├── services/               # Business logic
│   │   ├── jd_parser.py        # Extract skills from JD
│   │   └── company_analyzer.py # Analyze company data
│   │
│   ├── data/                   # Static data
│   │   ├── skills.json         # 200+ skill definitions
│   │   └── companies.json
│   │
│   └── db/                     # Database setup
│       ├── database.py         # SQLAlchemy config
│       └── init_db.py          # Migrations
```

---

## Phases Implementation

### Phase 1: Extension UI & Basic Backend
**Status**: ✅ Complete

**Components**:
- Chrome extension sidebar with job detail display
- Backend API endpoints for job parsing
- Basic skill extraction from LinkedIn/Indeed

**Files**:
- `extension/manifest.json` - Extension permissions & configuration
- `extension/side_panel/focusbar.html` - UI layout
- `backend/routers/job.py` - Job parsing endpoints
- `backend/services/jd_parser.py` - JD extraction logic

---

### Phase 2: Multi-Site Job Parsing → Universal
**Status**: ✅ Complete

**Upgrade**: Originally supported only LinkedIn/Naukri. Now works on **ANY website**.

**Key Components**:
- `extension/content-scripts/universal-parser.js` (216 lines)
  - Generic DOM heuristics to find job title, company, description
  - Works on Accenture career pages, generic job boards, LinkedIn, etc.
  - Auto-detects when page contains job information

- `backend/services/jd_parser.py` - Enhanced with:
  - `_extract_unknown_skills()` function for dynamic skill detection
  - Uses regex patterns to find domain-specific skills not in database
  - Handles specialized terms (Siemens eMeter, EnergyIP MDMS, etc.)

- `backend/data/skills.json` - Expanded from 43 → 200+ skills
  - Includes enterprise systems: SAP, Oracle, Salesforce
  - Domain-specific: Energy (MDMS, AMI), Banking, Healthcare
  - Emerging tech: Kubernetes, Terraform, GraphQL

**Example - Accenture Job**:
- **Input**: Accenture career page with Siemens eMeter role description
- **Processing**: Universal parser extracts title, company, JD text
- **Output**: Identifies Siemens eMeter, EnergyIP, Java, Configuration MDMS as required skills
- **Matching**: Compares against user's profile

---

### Phase 3: Q&A Backend & Skill Persistence
**Status**: ✅ Complete

**Database Integration**:
- `backend/models/qa_response.py` - Stores user Q&A responses
- `backend/models/user_skill.py` - User's skill profile with experience levels

**Endpoints**:
- `POST /qa/generate-questions` - Generate context-aware questions for skill gaps
- `POST /qa/save-responses` - Persist Q&A responses to database
- `POST /qa/bulk-update-skills` - Update user skills in bulk from Q&A session
- `GET /qa/user/{user_id}/responses` - Retrieve Q&A history
- `GET /qa/user/{user_id}/skills` - Get user's skill profile

**How It Works**:
1. Job page loaded → Extension detects job requirements
2. System compares with user's stored skills
3. Generates questions for mandatory skills user lacks
4. User answers Q&A modal
5. Responses persisted to database
6. User skill profile updated for future job matching

**Example Flow**:
```
Job: "Spring Boot Developer"
Required Skills: Java (3+ yrs), Spring Boot (2+ yrs), AWS

User Profile: Java (1 yr), No Spring Boot, No AWS

Gap Analysis → Q&A Generation:
- Q1: "Do you have practical experience with Spring Boot?"
- Q2: "Have you worked on Spring Boot projects?"
- Q3: "Can you describe hands-on project experience?"

User Answers:
- "No experience with Spring Boot"
- Responses saved → User skill profile updated
```

---

### Phase 4: Universal Content Extraction
**Status**: ✅ Complete

**Implementation**: `extension/content-scripts/universal-parser.js`

**Features**:
- ✅ Extracts from LinkedIn job postings
- ✅ Extracts from Indeed listings
- ✅ Extracts from company career pages (Accenture, Google, etc.)
- ✅ Extracts from custom job boards
- ✅ MutationObserver to auto-detect when content changes

**Heuristics Used**:
1. Find largest text container (usually the JD)
2. Extract title from `<h1>` or first large heading
3. Locate company name from page context
4. Parse requirements from structured lists or paragraphs
5. Handle common JD patterns (Required vs Nice-to-have)

---

### Phase 5: Company Insights & Aggregation
**Status**: ✅ Complete (Backend)

**Models**:
- `backend/models/company.py` - Aggregated company data
- Fields: locations, tech_stack, typical_roles, salary_bands, industries

**Endpoints**:
- `POST /company/analyse` - Extract insights from single job posting
- `GET /company/profile/{name}` - Company profile with aggregated data
- `GET /company/{name}/roles` - Typical career paths
- `GET /company/{name}/tech-stack` - Required tech by role
- `GET /company/{name}/salary` - Salary band estimates
- `GET /company/search?q=...` - Company search (autocompletion)

**Data Aggregation**:
- Analyzes multiple job postings for same company
- Builds aggregate profile of tech stack, roles, salary
- Tracks trends (e.g., "Company X shifting from Java to Python")

**Example**:
```json
{
  "company": "Accenture",
  "locations": ["Bangalore", "Hyderabad", "Remote"],
  "tech_stack": ["Java", "Python", "AWS", "Docker", "Kubernetes"],
  "typical_roles": ["Software Engineer", "DevOps", "Backend Developer"],
  "salary_bands": {
    "entry": "₹6L - ₹14L",
    "mid": "₹15L - ₹28L",
    "senior": "₹30L - ₹50L+"
  },
  "jobs_analyzed": 47
}
```

---

### Phase 6: Coding Session Tracker
**Status**: ✅ Complete (Backend)

**Models**:
- `backend/models/coding_session.py` - Tracks individual coding sessions

**Endpoints**:
- `POST /coding-session/session/log` - Log a coding session with problems solved
- `GET /coding-session/user/{user_id}/stats` - Overall coding statistics
- `GET /coding-session/user/{user_id}/sessions` - Recent sessions (paginated)
- `GET /coding-session/user/{user_id}/topic-stats` - Performance by topic (Array, DP, Graphs, etc.)
- `GET /coding-session/platform-parser/{platform}` - Info on connecting LeetCode/GFG/Codeforces
- `POST /coding-session/sync/leetcode` - Sync LeetCode profile (placeholder)
- `POST /coding-session/sync/gfg` - Sync GFG profile (placeholder)
- `POST /coding-session/sync/codeforces` - Sync Codeforces via official API (placeholder)

**Statistics Tracked**:
- Total problems solved by difficulty (Easy/Medium/Hard)
- Problems solved by topic (Arrays, Strings, DP, Graphs, Trees, etc.)
- Current coding streak (consecutive days)
- Accuracy rate (problems solved / attempted)
- Average solve time per topic
- Platform-wise activity (LeetCode vs GFG vs Codeforces)

**Example Session**:
```json
{
  "platform": "leetcode",
  "session_type": "practice",
  "duration_minutes": 120,
  "problems": [
    {
      "name": "Two Sum",
      "topic": "arrays",
      "difficulty": "easy",
      "status": "accepted",
      "solve_time": 15
    },
    {
      "name": "LRU Cache",
      "topic": "design",
      "difficulty": "medium",
      "status": "accepted",
      "solve_time": 45
    }
  ],
  "stats": {
    "problems_attempted": 2,
    "problems_solved": 2,
    "accuracy": 100%
  }
}
```

---

### Phase 7: Gap Analysis & Learning Roadmap
**Status**: ✅ Complete (Backend)

**Models**: Uses existing User, UserSkill, Skill models

**Endpoints**:
- `POST /gap-analysis/analyze` - Analyze skill gaps for a job
- `POST /gap-analysis/roadmap` - Generate personalized learning roadmap
- `GET /gap-analysis/job-match/{user_id}?job_title=...&company=...` - Calculate match score
- `POST /gap-analysis/resources/{skill}` - Get learning resources for a skill
- `POST /gap-analysis/subscribe-resource` - Subscribe to a resource for tracking

**Gap Analysis Algorithm**:
1. Load user's current skills from database
2. Parse job requirements (mandatory vs nice-to-have)
3. For each required skill:
   - Check if user has it
   - If user has it, check experience level matches requirement
   - Assign gap severity: critical/high/medium/low
4. Estimate learning time for each gap (based on severity)
5. Calculate overall match confidence

**Roadmap Generation**:
```
Phase 1 (Week 1-2): Foundation - Critical mandatory skills
  - Java Basics (3 hrs/day)
  - SQL Fundamentals (2 hrs/day)
  Daily focus: Understand core concepts, write simple programs

Phase 2 (Week 3-4): Skill Development - High priority gaps
  - Spring Boot projects (2 hrs/day)
  - AWS basics (1.5 hrs/day)
  Daily focus: Build projects, solve problems

Phase 3 (Week 5-6): Interview Preparation
  - System design (2 hrs/day)
  - Behavioral prep (1 hr/day)
  Focus: Mock interviews, revision

Phase 4 (Week 7+): Final Review & Application
  - Concept revision (1 hr/day)
  - Apply to jobs
```

**Learning Resources**:
- Curated from Udemy, Coursera, YouTube, GeeksforGeeks, LeetCode
- Includes cost, difficulty level, estimated duration
- Links to free vs paid courses

**Example Output**:
```json
{
  "user_id": 1,
  "job_title": "Application Developer",
  "company": "Accenture",
  "total_gaps": 3,
  "critical_gaps": ["Siemens eMeter"],
  "high_priority_gaps": ["EnergyIP", "Configuration MDMS"],
  "total_learning_hours": 120,
  "estimated_weeks": 6,
  "roadmap_phases": [...],
  "resources": [
    {
      "skill": "Siemens eMeter",
      "title": "Siemens eMeter Fundamentals",
      "platform": "Udemy",
      "difficulty": "intermediate",
      "duration_hours": 40,
      "cost": "paid"
    }
  ]
}
```

---

### Phase 8: Application Outcome Tracking
**Status**: ✅ Complete (Backend)

**Models**:
- `backend/models/application.py` - Job application records

**Endpoints**:
- `POST /applications/track` - Log a new job application
- `PUT /applications/update/{app_id}` - Update application status
- `GET /applications/user/{user_id}/applications` - All applications
- `GET /applications/user/{user_id}/analytics` - Analytics dashboard
- `GET /applications/user/{user_id}/pipeline` - Kanban-like pipeline view
- `GET /applications/user/{user_id}/company-stats` - Stats by company
- `GET /applications/user/{user_id}/timeline` - Chronological timeline
- `POST /applications/user/{user_id}/export` - Export as CSV/JSON
- `GET /applications/insights/{user_id}` - AI-powered insights

**Tracked Data**:
- Company, job title, job URL
- Application date, follow-up date, interview date
- Status: Applied → Shortlisted → Interviewed → Offered/Rejected
- Match score (0-100)
- User notes

**Analytics Provided**:
- Total applications count
- Status distribution (pie chart data)
- Success rate (offers / applications)
- Average response time (days)
- Conversion funnel: Applied → Shortlist → Interview → Offer
- Company-wise performance

**Pipeline View (Kanban)**:
```
Applied (45)     Shortlisted (12)   Interviewed (5)   Offered (2)
┌─────────────┐  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│ Accenture   │  │ TCS         │   │ Google      │   │ Microsoft   │
│ Sr. Dev     │  │ Backend Dev │   │ SDE II      │   │ SDE III     │
│ Match: 65%  │  │ Match: 85%  │   │ Match: 90%  │   │ Match: 95%  │
└─────────────┘  └─────────────┘   └─────────────┘   └─────────────┘
```

**AI Insights**:
- "Your success rate (15%) is above average - keep applying!"
- "TCS is your strongest company (3/4 interviews) - focus here"
- "Apply more to overcome low volume"
- "Improve resume/interview skills - high drop at shortlist stage"

---

## Database Schema

### Tables

**users**
```sql
id, name, email, created_at, updated_at
```

**user_skills**
```sql
id, user_id, skill_id, duration_bucket, project_notes, created_at
```

**skills**
```sql
id, name, category, proficiency_level
```

**qa_responses**
```sql
id, user_id, user_skill_id, skill_name, has_experience, duration_bucket,
project_notes, job_title, job_company, answered_at
```

**companies**
```sql
id, name, industry, company_size, locations (JSON), typical_roles (JSON),
tech_stack (JSON), salary_entry, salary_mid, salary_senior,
jobs_analyzed, last_updated
```

**coding_sessions**
```sql
id, user_id, platform, session_type, session_date, duration_minutes,
problems_count, problems_solved, problems_data (JSON), notes
```

**applications**
```sql
id, user_id, company, job_title, jd_url, status, application_date,
follow_up_date, interview_date, match_score, notes, last_updated
```

---

## API Summary

### Job Parsing (Phase 1-2)
```
POST   /job/parse              - Parse job posting from URL/text
GET    /job/{job_id}           - Get job details
POST   /job/extract-skills     - Extract skills from JD
```

### Q&A & Skill Management (Phase 3)
```
POST   /qa/generate-questions         - Generate Q&A questions
POST   /qa/save-responses             - Save Q&A responses
POST   /qa/bulk-update-skills         - Bulk update user skills
GET    /qa/user/{user_id}/skills      - Get user skills profile
```

### Company Insights (Phase 5)
```
POST   /company/analyse                      - Analyze job for company data
GET    /company/profile/{name}               - Company profile
GET    /company/{name}/roles                 - Typical roles
GET    /company/{name}/tech-stack            - Tech stack by role
GET    /company/{name}/salary                - Salary bands
GET    /company/search?q={query}             - Search companies
```

### Coding Sessions (Phase 6)
```
POST   /coding-session/session/log              - Log session
GET    /coding-session/user/{id}/stats          - User stats
GET    /coding-session/user/{id}/topic-stats    - Topic performance
GET    /coding-session/platform-parser/{name}  - Platform info
```

### Gap Analysis (Phase 7)
```
POST   /gap-analysis/analyze              - Analyze gaps
POST   /gap-analysis/roadmap              - Generate roadmap
GET    /gap-analysis/job-match/{user_id}  - Match score
POST   /gap-analysis/resources/{skill}    - Get resources
```

### Application Tracking (Phase 8)
```
POST   /applications/track                           - Log application
PUT    /applications/update/{id}                     - Update status
GET    /applications/user/{user_id}/applications     - All apps
GET    /applications/user/{user_id}/analytics        - Analytics
GET    /applications/user/{user_id}/pipeline         - Pipeline view
GET    /applications/user/{user_id}/company-stats    - Company stats
GET    /applications/user/{user_id}/timeline         - Timeline
GET    /applications/insights/{user_id}              - Insights
```

---

## Frontend Integration

### Chrome Extension Components

**side_panel/focusbar.html**:
- Job details card with title, company, JD
- Skill matching section (Mandatory, Nice-to-have, Your match)
- Covered/Missing skills breakdown
- Gap Analysis & Recommendations section
- Application outcome tracking buttons
- Refine Skills Q&A button for Phase 3

**content-scripts/universal-parser.js**:
- Detects job posting on any website
- Extracts title, company, job description
- Sends to backend for skill extraction
- Updates sidebar with results

**background/service-worker.js**:
- Listens for page navigation
- Detects when user is on a job page
- Triggers content script injection
- Manages popup notifications

---

## Testing

### Unit Tests
```bash
# Test phase 3 Q&A endpoints
python -m pytest backend/routers/test_qa.py -v

# Test company analyzer
python -m pytest backend/services/test_company_analyzer.py -v

# Test gap analysis
python -m pytest backend/routers/test_gap_analysis.py -v

# Test application tracking
python -m pytest backend/routers/test_application_tracking.py -v
```

### Integration Tests
```bash
# Test full flow: job posting → skill extraction → gap analysis → roadmap
python -m pytest backend/tests/test_full_pipeline.py -v
```

### Manual Testing
```bash
# Start backend
cd backend
python -m uvicorn main:app --reload

# Load extension in Chrome
- Open chrome://extensions
- Enable Developer mode
- Click "Load unpacked"
- Select extension/ folder

# Test on job page
- Navigate to LinkedIn/Accenture/Indeed job posting
- Sidebar should populate with parsed data
```

---

## Deployment

### Backend Deployment
```bash
# Production with Gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker backend.main:app --bind 0.0.0.0:8000

# Docker
docker build -t drive2hire-backend .
docker run -p 8000:8000 drive2hire-backend
```

### Extension Distribution
```bash
# Generate extension package
cd extension
zip -r Drive2Hire.zip . -x "*.git*" "node_modules/*"

# Upload to Chrome Web Store
# Follow: https://developer.chrome.com/docs/webstore/publish/
```

---

## Future Enhancements

### Phase 6.5: Coding Platform Sync
- [ ] LeetCode API integration (GraphQL)
- [ ] GeeksforGeeks scraper/API
- [ ] Codeforces API client
- [ ] Real-time problem sync

### Phase 7.5: Smart Resume Parser
- [ ] PDF/DOCX parsing
- [ ] Extract experience, education, projects
- [ ] Auto-fill user profile
- [ ] Resume → Job matching

### Phase 8.5: Interview Preparation
- [ ] Mock interview scheduling
- [ ] Behavioral Q&A bank
- [ ] System design problem sets
- [ ] Recording & analysis

### AI Enhancements
- [ ] Skill recommendation engine
- [ ] Personalized interview questions
- [ ] Resume optimization suggestions
- [ ] Job role prediction based on profile

---

## Troubleshooting

### Extension not detecting job pages
- Check manifest.json host_permissions
- Verify universal-parser.js is injected
- Check browser console for errors

### Skills not extracting correctly
- Verify skills.json has comprehensive list
- Check jd_parser.py regex patterns
- Test with _extract_unknown_skills() function

### Company data not aggregating
- Ensure company_analyzer.py is analyzing multiple postings
- Check company.py model schema
- Verify database migrations applied

---

## Contributors

- **Yamuna B** - Lead developer
- **Copilot** - Implementation assistance

---

## License

MIT License - See LICENSE file for details

---

## Support

For issues and feature requests:
- GitHub Issues: https://github.com/Yamuna-b/Drive2Hire
- Email: yamuna.b@example.com
