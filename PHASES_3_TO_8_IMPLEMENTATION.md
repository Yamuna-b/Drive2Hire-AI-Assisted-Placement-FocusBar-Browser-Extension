# Complete Phases 3-8 Implementation Plan

## Phase 3: Complete Q&A Skill Refinement (IN_PROGRESS → COMPLETE)

### Current Status
- ✅ Backend Q&A endpoints exist (`/qa/generate-questions`)
- ✅ Frontend modal exists
- ❌ Database persistence missing
- ❌ User profile management incomplete
- ❌ Skill level tracking not integrated

### What to Add

**1. Database Models (Already exist, need to enhance)**
```python
# backend/models/user_skill.py - ENHANCE
- Add: skill_level (beginner/intermediate/advanced/expert)
- Add: last_updated timestamp
- Add: qa_responses (relationship to QAResponse model)

# NEW: backend/models/qa_response.py
class QAResponse(Base):
    user_skill_id = ForeignKey(user_skills.id)
    has_experience = Boolean
    duration_bucket = String  # "<1 year", "1-2 years", "2+ years"
    project_notes = Text
    answered_at = DateTime
```

**2. New Endpoints**
```
POST /user/profile
- Get/save user profile (name, email, skills, experience)

POST /user/skills/update
- Update individual skill (level, duration, notes)

POST /qa/responses/save
- Persist Q&A responses to database

GET /user/skills
- Get all user skills with levels and notes

POST /user/skills/bulk-update
- Update multiple skills from Q&A session
```

**3. Frontend Integration**
```javascript
// In focusbar.js - enhance Q&A modal
- After "Save & Re-analyze", call /user/skills/bulk-update
- Store user_id in chrome.storage.local
- Auto-load user profile on panel open
- Show skill updates confirmation

// In service-worker.js
- Track user_id in session storage
- Manage authentication/user context
```

**4. Resume Parser** (NEW)
```python
# backend/routers/resume.py - COMPLETE
POST /user/resume/upload
- Parse uploaded resume (PDF/DOCX)
- Extract: Education, Experience, Skills, Projects
- Auto-populate user profile + skills
- Provide accuracy score for extracted data
```

---

## Phase 5: Company Insights & Analytics (NOT_STARTED → COMPLETE)

### Requirements
Extract company info from job postings and aggregate data

### Implementation

**1. New Backend Models**
```python
# backend/models/company.py - ENHANCE
class Company(Base):
    name = String (unique)
    website = String
    locations = JSON
    tech_stack = JSON  # [Python, Java, React, ...]
    typical_roles = JSON  # [SDE, Frontend, Backend, ...]
    salary_entry = String  # "₹6L-14L"
    salary_mid = String
    salary_senior = String
    company_size = String  # Startup, SMB, Enterprise
    founded_year = Integer
    industry = String  # Software, Finance, Energy, etc.
    last_updated = DateTime
```

**2. Extraction Logic**
```python
# backend/services/company_analyzer.py (NEW)

def extract_company_info(job_data: dict) -> dict:
    """Extract company info from job posting"""
    return {
        "name": job_data["company"],
        "roles": extract_roles_from_jd(job_data["jd"]),
        "tech_stack": extract_tech_from_jd(job_data["jd"]),
        "salary": extract_salary_from_jd(job_data["jd"]),
        "location": extract_location_from_job(job_data),
    }

def aggregate_company_data(company_jobs: list) -> dict:
    """Aggregate data from multiple job postings"""
    # Common tech stack across roles
    # Salary ranges per level
    # Typical career paths
    # Growth opportunities
```

**3. New Endpoints**
```
GET /company/{company_name}
- Return company profile with all insights

POST /company/analyse
- Extract company info from job posting

GET /company/search
- Search companies (autocompletion)

GET /company/{company_name}/roles
- Typical roles and growth paths

GET /company/{company_name}/tech-stack
- Technology stack + skill requirements per role
```

**4. Frontend - Company Tab**
```html
<!-- extension/side_panel/company-tab.html -->
<div class="company-section">
  <h2>Company Insights</h2>
  
  <div class="company-card">
    <h3>${company_name}</h3>
    <p class="industry">${industry}</p>
  </div>
  
  <section class="tech-stack">
    <h4>Tech Stack</h4>
    <div class="skills">
      ${tech_stack.map(tech => `<span class="skill-tag">${tech}</span>`)}
    </div>
  </section>
  
  <section class="roles">
    <h4>Typical Roles</h4>
    <ul>
      ${typical_roles.map(role => `<li>${role}</li>`)}
    </ul>
  </section>
  
  <section class="salary">
    <h4>Salary Bands (INR/year)</h4>
    <div class="salary-grid">
      <div>Entry Level: ${salary_entry}</div>
      <div>Mid Level: ${salary_mid}</div>
      <div>Senior: ${salary_senior}</div>
    </div>
  </section>
  
  <section class="locations">
    <h4>Office Locations</h4>
    <ul>${locations.map(loc => `<li>${loc}</li>`)}</ul>
  </section>
</div>
```

**5. UI Update in focusbar.js**
```javascript
// Add company analysis trigger
if (analysis.company) {
  fetch(`/company/analyse`, {
    method: 'POST',
    body: JSON.stringify(analysis)
  })
  .then(res => res.json())
  .then(companyData => {
    chrome.storage.local.set({ lastCompanyData: companyData })
  })
}
```

---

## Phase 6: Coding Session Tracker (NOT_STARTED → COMPLETE)

### Requirements
Track coding practice across LeetCode, GFG, Codeforces

### Implementation

**1. New Models**
```python
# backend/models/coding_account_sync.py - ENHANCE
class CodingAccountSync(Base):
    user_id = ForeignKey
    platform = String  # "leetcode", "gfg", "codeforces"
    username = String
    last_synced = DateTime
    profile_url = String
    problems_solved = Integer
    acceptance_rate = Float
    ranking = String

# backend/models/coding_session.py - ENHANCE
class CodingSession(Base):
    user_id = ForeignKey
    platform = String
    problem_id = String
    difficulty = String  # Easy, Medium, Hard
    topic = String  # Array, String, DP, Tree, etc.
    status = String  # Attempted, Solved, Skipped
    time_spent = Integer  # minutes
    submission_count = Integer
    solution_link = String
    session_date = DateTime
    notes = Text

class TopicStats(Base):
    user_id = ForeignKey
    topic = String
    total_problems = Integer
    solved = Integer
    accuracy = Float
    time_avg = Integer
```

**2. Platform Parsers**
```python
# backend/services/leetcode_parser.py (NEW)
def extract_leetcode_profile(username: str):
    """Fetch from LeetCode API"""
    # Uses LeetCode GraphQL API
    # Returns: solved problems, acceptance rate, contest rating
    
def extract_leetcode_submissions(user_id: int):
    """Parse recent submissions"""
    # Returns: problem details, solution code, status
    
def categorize_by_topic(submissions):
    # Group: Arrays, Strings, DP, Trees, Graphs, etc.
    # Calculate accuracy per topic

# backend/services/gfg_parser.py (NEW)
def extract_gfg_profile(username: str):
    """GeeksforGeeks profile parsing"""
    # Returns: problems solved, score, ranking
    
# backend/services/codeforces_parser.py (NEW)
def extract_codeforces_profile(handle: str):
    """Codeforces API integration"""
    # Returns: contests, rating, problems solved
```

**3. New Endpoints**
```
POST /coding/account/connect
- Link LeetCode/GFG/Codeforces account
- Store username + sync

GET /coding/profile
- Get aggregated stats across all platforms

GET /coding/sessions
- List recent coding sessions

POST /coding/session/log
- Manually log session (if auto-sync unavailable)

GET /coding/topics
- Topic-wise stats (accuracy, problems, avg time)

GET /coding/progress
- Weekly/monthly progress chart data

GET /coding/recommendations
- Recommend topics/problems based on weak areas
```

**4. Frontend - Coding Tab**
```html
<!-- extension/side_panel/coding-tab.html -->
<div class="coding-section">
  <h2>Coding Practice</h2>
  
  <div class="session-timer">
    <div class="timer-display">00:45:30</div>
    <button id="start-session">Start Session</button>
    <button id="end-session" disabled>End Session</button>
    <input type="text" id="session-problem" placeholder="Problem link or title">
  </div>
  
  <div class="platform-stats">
    <div class="leetcode">
      <h4>LeetCode</h4>
      <p>Solved: 150/2500</p>
      <p>Acceptance: 87%</p>
      <a href="link-account">Link Account</a>
    </div>
    
    <div class="gfg">
      <h4>GeeksforGeeks</h4>
      <p>Score: 2500</p>
      <p>Ranking: #1234</p>
    </div>
    
    <div class="codeforces">
      <h4>Codeforces</h4>
      <p>Rating: 1500</p>
      <p>Contests: 12</p>
    </div>
  </div>
  
  <div class="topics-breakdown">
    <h4>Topic-wise Performance</h4>
    <div class="topic-stats">
      <div class="topic">
        <span>Arrays</span>
        <span class="solved">24/30</span>
        <span class="accuracy">80%</span>
      </div>
      <div class="topic">
        <span>Dynamic Programming</span>
        <span class="solved">12/25</span>
        <span class="accuracy">48%</span>
      </div>
      <!-- More topics -->
    </div>
  </div>
  
  <div class="weak-areas">
    <h4>Areas to Focus</h4>
    <ul>
      <li>Dynamic Programming - 48% accuracy</li>
      <li>Graph Algorithms - 65% accuracy</li>
    </ul>
  </div>
</div>
```

**5. Session Timer Script**
```javascript
// extension/content-scripts/coding-timer.js
// Auto-detect when on LeetCode/GFG/Codeforces
// Start timer when user opens problem
// Log session automatically on page close
// Sync with backend
```

---

## Phase 7: Gap Analysis & Prep Recommendations (NOT_STARTED → COMPLETE)

### Requirements
Generate learning roadmap based on skill gaps

### Implementation

**1. Gap Analysis Engine**
```python
# backend/services/gap_analyzer.py (NEW)

def analyze_skill_gaps(job_requirements: list, user_skills: list):
    """Calculate gaps"""
    gaps = {
        "critical": [],      # Not have, required
        "experience": [],    # Have, but less duration
        "weak": [],          # Have, but weak level
        "stretch": []        # Nice-to-have, not have
    }
    return gaps

def generate_roadmap(gaps: dict, timeline_weeks: int):
    """Create learning plan"""
    return {
        "week_1": ["Topic 1", "Topic 2"],
        "week_2": ["Practice 1", "Project 1"],
        "resources": [...]
    }
```

**2. Resource Database**
```python
# backend/data/resources.json
{
  "resources": [
    {
      "skill": "Python",
      "type": "course",
      "title": "Python for Beginners",
      "platform": "YouTube/Udemy",
      "duration_hours": 10,
      "difficulty": "beginner",
      "free": true,
      "url": "..."
    },
    {
      "skill": "System Design",
      "type": "book",
      "title": "Designing Data-Intensive Applications",
      "difficulty": "advanced",
      "cost": 50
    }
  ]
}
```

**3. Endpoints**
```
POST /analysis/gap-analysis
- Input: job_data, user_skills
- Output: gaps categorized by severity

POST /analysis/learning-roadmap
- Generate timeline-based learning plan

GET /resources/{skill}
- Get resources for a skill

POST /analysis/track-progress
- Update progress on learning plan
```

**4. Frontend - Gap Analysis Tab**
```html
<div class="gap-analysis">
  <h2>Gap Analysis & Prep Plan</h2>
  
  <div class="gap-summary">
    <h3>Skills Analysis for ${job_title}</h3>
    
    <div class="gap-category critical">
      <h4>🔴 Critical Gaps (Learn before applying)</h4>
      <ul>
        <li>Siemens eMeter - 3 years required, you have: 0</li>
        <li>EnergyIP MDMS - 2+ years required, you have: 0</li>
      </ul>
    </div>
    
    <div class="gap-category experience">
      <h4>🟡 Experience Gaps</h4>
      <ul>
        <li>Java - 2+ years required, you have: 1 year</li>
      </ul>
    </div>
    
    <div class="gap-category weak">
      <h4>🟢 Skills to Strengthen</h4>
      <ul>
        <li>REST APIs - weak level, need intermediate</li>
      </ul>
    </div>
  </div>
  
  <div class="roadmap">
    <h3>8-Week Learning Roadmap</h3>
    
    <div class="week">
      <h4>Week 1-2: Foundations</h4>
      <ul>
        <li>
          <strong>Siemens eMeter Fundamentals</strong>
          <a href="#">YouTube Playlist (8 hours)</a> - FREE
        </li>
        <li>
          <strong>Smart Meter Technology</strong>
          <a href="#">Udemy Course</a> - $15
        </li>
      </ul>
    </div>
    
    <div class="week">
      <h4>Week 3-4: Deep Dive</h4>
      <ul>
        <li>Complete Siemens eMeter online certification</li>
        <li>Hands-on lab: Configure test MDMS system</li>
      </ul>
    </div>
    
    <div class="week">
      <h4>Week 5-6: Projects</h4>
      <ul>
        <li>Build demo EnergyIP application</li>
        <li>Practice problem sets (LeetCode)</li>
      </ul>
    </div>
    
    <div class="week">
      <h4>Week 7-8: Interview Prep</h4>
      <ul>
        <li>Mock interviews</li>
        <li>Review Accenture's tech stack</li>
      </ul>
    </div>
  </div>
  
  <div class="resources-recommended">
    <h3>Recommended Resources</h3>
    ${resources.map(r => `
      <div class="resource">
        <span class="type">${r.type}</span>
        <span class="title">${r.title}</span>
        <span class="duration">${r.duration}</span>
        <span class="cost">${r.free ? 'FREE' : '$' + r.cost}</span>
      </div>
    `)}
  </div>
</div>
```

---

## Phase 8: Application Outcome Tracking (NOT_STARTED → COMPLETE)

### Requirements
Track applications and build career pipeline

### Implementation

**1. New Models**
```python
# backend/models/job_outcome.py - ENHANCE
class JobOutcome(Base):
    user_id = ForeignKey
    job_id = ForeignKey  # Link to job posting
    company = String
    position = String
    status = String  # Applied, Shortlisted, Interview, Offer, Rejected
    applied_at = DateTime
    follow_up_date = DateTime
    notes = Text
    salary_offered = Integer
    offer_accepted = Boolean
    rejection_reason = String
    
class ApplicationPipeline(Base):
    user_id = ForeignKey
    company = String
    stage = String  # funnel stage
    applications = Integer
    interviews = Integer
    offers = Integer
```

**2. Endpoints**
```
POST /application/log
- Log new application

PATCH /application/{id}
- Update application status

GET /application/dashboard
- Pipeline stats: Applied → Interview → Offer

GET /application/timeline
- Chronological view of all applications

POST /application/follow-up
- Set reminders for follow-up

GET /application/analytics
- Success rates by company/role
- Average time to response
- Offer statistics
```

**3. Frontend - Application Tracking Tab**
```html
<div class="applications">
  <h2>📋 Application Tracking</h2>
  
  <div class="quick-log">
    <button id="log-application">+ Log New Application</button>
  </div>
  
  <div class="pipeline-chart">
    <div class="stage applied">
      <span class="count">12</span>
      <span class="label">Applied</span>
    </div>
    <div class="arrow">→</div>
    <div class="stage shortlisted">
      <span class="count">5</span>
      <span class="label">Shortlisted</span>
    </div>
    <div class="arrow">→</div>
    <div class="stage interview">
      <span class="count">3</span>
      <span class="label">Interview</span>
    </div>
    <div class="arrow">→</div>
    <div class="stage offer">
      <span class="count">1</span>
      <span class="label">Offer</span>
    </div>
  </div>
  
  <div class="applications-list">
    <h3>Recent Applications</h3>
    
    <div class="application-card">
      <div class="status applied">Applied</div>
      <div class="details">
        <h4>Software Engineer</h4>
        <p class="company">Accenture</p>
        <p class="date">Applied: Sep 1, 2026</p>
      </div>
      <div class="actions">
        <select onchange="updateStatus(event)">
          <option>Applied</option>
          <option>Shortlisted</option>
          <option>Interview</option>
          <option>Offer</option>
          <option>Rejected</option>
        </select>
      </div>
    </div>
    
    <div class="application-card">
      <div class="status interview">Interview</div>
      <div class="details">
        <h4>Frontend Developer</h4>
        <p class="company">Flipkart</p>
        <p class="date">Applied: Aug 28, 2026</p>
        <p class="interview-date">Interview: Sep 5, 2026</p>
      </div>
    </div>
  </div>
  
  <div class="analytics">
    <h3>📊 Statistics</h3>
    <div class="stats-grid">
      <div class="stat">
        <span class="number">12</span>
        <span class="label">Total Applications</span>
      </div>
      <div class="stat">
        <span class="number">42%</span>
        <span class="label">Response Rate</span>
      </div>
      <div class="stat">
        <span class="number">3</span>
        <span class="label">Interviews Scheduled</span>
      </div>
      <div class="stat">
        <span class="number">8%</span>
        <span class="label">Offer Rate</span>
      </div>
    </div>
  </div>
</div>
```

---

## Summary of All Phases

| Phase | Feature | Status | Effort |
|-------|---------|--------|--------|
| 1 | Extension + Backend | ✅ COMPLETE | Done |
| 2 | Multi-site Job Parsing | ✅ COMPLETE | Done |
| 3 | Q&A + Profile Mgmt | 🟡 IN_PROGRESS | Database + endpoints |
| 4 | Universal Extraction | ✅ COMPLETE | Done |
| 5 | Company Insights | ❌ TODO | New tab + aggregation |
| 6 | Coding Session Tracker | ❌ TODO | Platform parsers + UI |
| 7 | Gap Analysis & Roadmap | ❌ TODO | Recommendation engine |
| 8 | Application Tracking | ❌ TODO | Pipeline dashboard |

---

## Implementation Timeline

- **Phase 3:** 2-3 hours (DB + endpoints)
- **Phase 5:** 3-4 hours (Company aggregation + UI)
- **Phase 6:** 4-5 hours (Platform parsers + session tracking)
- **Phase 7:** 2-3 hours (Roadmap generation)
- **Phase 8:** 2-3 hours (Application dashboard)

**Total:** ~14-18 hours of comprehensive implementation

---

## Key Design Principles

1. **Modular**: Each phase builds on previous
2. **Data-driven**: Aggregate real job data
3. **User-centric**: Beautiful UI with actionable insights
4. **Scalable**: Database models support growth
5. **Extensible**: Easy to add new platforms/features
