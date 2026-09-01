document.addEventListener('DOMContentLoaded', () => {
  const content = document.getElementById('content');
  const statusEl = document.getElementById('backend-status');
  const tabs = document.querySelectorAll('nav ul li');
  let activeTab = 'Job';
  let currentUserId = 1; // Default user ID

  function skillList(label, items, className) {
    if (!items || items.length === 0) {
      return `<div class="skill-group"><strong>${label}</strong><p class="muted">None detected</p></div>`;
    }
    const tags = items.map((s) => `<span class="tag ${className}">${s}</span>`).join('');
    return `<div class="skill-group"><strong>${label}</strong><div class="tags">${tags}</div></div>`;
  }

  // ---------- Q&A Modal ----------
  function createModal() {
    const overlay = document.createElement('div');
    overlay.id = 'qa-modal-overlay';
    overlay.style.position = 'fixed';
    overlay.style.top = '0';
    overlay.style.left = '0';
    overlay.style.width = '100%';
    overlay.style.height = '100%';
    overlay.style.background = 'rgba(0,0,0,0.5)';
    overlay.style.display = 'flex';
    overlay.style.alignItems = 'center';
    overlay.style.justifyContent = 'center';
    overlay.style.zIndex = '1000';

    const modal = document.createElement('div');
    modal.id = 'qa-modal';
    modal.style.background = '#fff';
    modal.style.padding = '1rem';
    modal.style.borderRadius = '8px';
    modal.style.maxWidth = '90%';
    modal.style.maxHeight = '80%';
    modal.style.overflowY = 'auto';
    overlay.appendChild(modal);
    document.body.appendChild(overlay);
    return { overlay, modal };
  }

  function showDurationModal(gapSkills) {
    const { overlay, modal } = createModal();
    const form = document.createElement('form');
    form.id = 'qa-form';
    modal.appendChild(document.createElement('h2')).innerText = 'Skill Experience Details';
    gapSkills.forEach((skillObj, idx) => {
      const container = document.createElement('div');
      container.style.marginBottom = '1rem';
      container.innerHTML = `
        <strong>${skillObj.name} (required: ${skillObj.required_duration})</strong><br/>
        <label>Do you have experience? 
          <select name="hasExp_${idx}" required>
            <option value="yes">Yes</option>
            <option value="no">No</option>
          </select>
        </label><br/>
        <label>Duration: 
          <select name="duration_${idx}" disabled>
            <option value="">Select…</option>
            <option value="<1 year"><1 year</option>
            <option value="1-2 years">1-2 years</option>
            <option value="2+ years">2+ years</option>
          </select>
        </label><br/>
        <label>Project notes (optional):<br/>
          <textarea name="notes_${idx}" rows="2" style="width:100%" disabled></textarea>
        </label>
      `;
      form.appendChild(container);
    });
    const submitBtn = document.createElement('button');
    submitBtn.type = 'submit';
    submitBtn.textContent = 'Save & Re‑analyze';
    submitBtn.style.marginTop = '1rem';
    form.appendChild(submitBtn);
    modal.appendChild(form);

    form.addEventListener('change', (e) => {
      const target = e.target;
      if (target.name && target.name.startsWith('hasExp_')) {
        const idx = target.name.split('_')[1];
        const durSelect = form.querySelector(`select[name="duration_${idx}"]`);
        const notesArea = form.querySelector(`textarea[name="notes_${idx}"]`);
        if (target.value === 'yes') {
          durSelect.disabled = false;
          notesArea.disabled = false;
        } else {
          durSelect.disabled = true;
          notesArea.disabled = true;
        }
      }
    });

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const data = new FormData(form);
      const updates = [];
      for (let i = 0; i < gapSkills.length; i++) {
        const hasExp = data.get(`hasExp_${i}`);
        if (hasExp === 'yes') {
          const duration = data.get(`duration_${i}`) || null;
          const notes = data.get(`notes_${i}`) || null;
          updates.push({ name: gapSkills[i].name, duration, notes });
        }
      }
      const stored = await chrome.storage.local.get('userSkills');
      const current = stored.userSkills || [];
      updates.forEach((u) => {
        const idx = current.findIndex((s) => s.name.toLowerCase() === u.name.toLowerCase());
        if (idx >= 0) {
          if (u.duration) current[idx].duration_bucket = u.duration;
          if (u.notes) current[idx].project_notes = u.notes;
        } else {
          current.push({ name: u.name, level: 'moderate', duration_bucket: u.duration, project_notes: u.notes });
        }
      });
      await chrome.storage.local.set({ userSkills: current });
      overlay.remove();
      chrome.runtime.sendMessage({ type: 'analyseCurrentTab' }, () => {});
    });
  }

  // ---------- Job Tab (Phase 1-4) ----------
  function renderJobTab(analysis, error) {
    if (error) {
      content.innerHTML = `
        <p class="error">${error}</p>
        <button id="btn-analyse" class="btn">Analyze current job page</button>
        <p class="muted">Open any job listing page (LinkedIn, Naukri, Indeed, Glassdoor, or any website) and click above.</p>
      `;
      bindAnalyseButton();
      return;
    }

    if (!analysis) {
      content.innerHTML = `
        <p>No job analyzed yet.</p>
        <button id="btn-analyse" class="btn">Analyze current job page</button>
        <p class="muted">Visit any job posting page, then click above.</p>
      `;
      bindAnalyseButton();
      return;
    }

    const match = analysis.match || { covered: [], weak: [], missing: [], needs_duration: [] };

    content.innerHTML = `
      <div class="job-snapshot">
        <h2>${analysis.title || 'Unknown role'}</h2>
        <p class="company">${analysis.company || 'Unknown company'}</p>
      </div>

      ${skillList('Mandatory skills', analysis.mandatory_skills.map(s => s.name), 'mandatory')}
      ${skillList('Nice-to-have skills', analysis.nice_to_have_skills.map(s => s.name), 'nice')}

      <div class="match-section">
        <strong>Your match</strong>
        ${skillList('Covered', match.covered, 'covered')}
        ${skillList('Weak', match.weak, 'weak')}
        ${skillList('Missing', match.missing, 'missing')}
      </div>

      <button id="btn-analyse" class="btn">Re-analyze current page</button>
      <button id="btn-qa" class="btn" style="margin-top: 0.5rem; background: #6366f1;">Refine Skills Q&A</button>
    `;
    bindAnalyseButton();
    
    const qaBtn = document.getElementById('btn-qa');
    if (qaBtn) {
      qaBtn.addEventListener('click', () => {
        triggerQASession(analysis);
      });
    }

    if (match.needs_duration && match.needs_duration.length) {
      showDurationModal(match.needs_duration);
    }
  }

  function triggerQASession(analysis) {
    chrome.storage.local.get('userSkills', (data) => {
      const userSkills = data.userSkills || [];
      fetch('http://127.0.0.1:8000/qa/generate-questions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          mandatory_skills: analysis.mandatory_skills,
          nice_to_have_skills: analysis.nice_to_have_skills,
          user_skills: userSkills
        })
      })
      .then(res => res.json())
      .then(qaData => {
        if (qaData.gap_skills && qaData.gap_skills.length > 0) {
          showDurationModal(qaData.gap_skills);
        } else {
          alert('No skills need refinement! You\'re well-matched for this role.');
        }
      })
      .catch(err => {
        alert('Q&A service error: ' + err.message);
      });
    });
  }

  function bindAnalyseButton() {
    const btn = document.getElementById('btn-analyse');
    if (!btn) return;

    btn.addEventListener('click', () => {
      btn.disabled = true;
      btn.textContent = 'Analyzing…';

      chrome.runtime.sendMessage({ type: 'analyseCurrentTab' }, (response) => {
        btn.disabled = false;
        btn.textContent = 'Re-analyze current page';

        if (chrome.runtime.lastError || !response?.ok) {
          if (activeTab === 'Job') {
            const msg = response?.error || chrome.runtime.lastError?.message || 'Analysis failed. Is the backend running?';
            renderJobTab(null, msg);
          }
          return;
        }

        if (activeTab === 'Job') {
          renderJobTab(response.analysis, null);
        }
      });
    });
  }

  // ---------- Company Tab (Phase 5 + Gap Analysis) ----------
  async function renderCompanyTab() {
    chrome.storage.local.get('lastJobAnalysis', async (data) => {
      const analysis = data.lastJobAnalysis;
      if (!analysis || !analysis.company) {
        content.innerHTML = `
          <div class="company-section">
            <h2>Company & Gap Analysis</h2>
            <p class="muted">Analyze a job page first to see company insights and skill gaps.</p>
            <button id="btn-analyze-company" class="btn">Analyze Current Job Page</button>
          </div>
        `;
        document.getElementById('btn-analyze-company')?.addEventListener('click', () => {
          chrome.runtime.sendMessage({ type: 'analyseCurrentTab' }, () => {
            renderCompanyTab();
          });
        });
        return;
      }

      content.innerHTML = '<p class="loading">Loading company insights and gap analysis...</p>';

      try {
        // Fetch real-time company data from internet
        const companyResponse = await fetch(`http://127.0.0.1:8000/company/analyze-realtime`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            company_name: analysis.company,
            job_title: analysis.title
          })
        });
        const companyData = await companyResponse.json();

        // Fetch gap analysis
        const gapResponse = await fetch('http://127.0.0.1:8000/gap-analysis/analyze', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_id: currentUserId,
            job_title: analysis.title,
            company: analysis.company,
            mandatory_skills: analysis.mandatory_skills || [],
            nice_to_have_skills: analysis.nice_to_have_skills || []
          })
        });
        const gapData = await gapResponse.json();

        // Fetch roadmap
        const roadmapResponse = await fetch('http://127.0.0.1:8000/gap-analysis/roadmap', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_id: currentUserId,
            job_title: analysis.title,
            company: analysis.company,
            mandatory_skills: analysis.mandatory_skills || [],
            nice_to_have_skills: analysis.nice_to_have_skills || []
          })
        });
        const roadmapData = await roadmapResponse.json();

        content.innerHTML = `
          <div class="company-section">
            <h2>Company & Gap Analysis</h2>
            
            <div class="company-card">
              <h3>${analysis.company}</h3>
              <p class="industry">${companyData.industry || 'Technology'}</p>
              <p class="company-size">${companyData.company_size || 'Enterprise'}</p>
              <p class="company-source">Data source: ${companyData.source || 'Real-time web search'}</p>
            </div>
            
            <section class="tech-stack">
              <h4>Tech Stack</h4>
              <div class="skills">
                ${(companyData.tech_stack || []).map(tech => `<span class="skill-tag">${tech}</span>`).join('')}
              </div>
            </section>
            
            <section class="roles">
              <h4>Typical Roles</h4>
              <ul>
                ${(companyData.typical_roles || []).map(role => `<li>${role}</li>`).join('')}
              </ul>
            </section>
            
            <section class="salary">
              <h4>Salary Bands (INR/year)</h4>
              <div class="salary-grid">
                <div class="salary-tier">
                  <span class="level">Entry Level</span>
                  <span class="amount">${companyData.salary_entry || '₹6L - ₹14L'}</span>
                </div>
                <div class="salary-tier">
                  <span class="level">Mid Level</span>
                  <span class="amount">${companyData.salary_mid || '₹15L - ₹28L'}</span>
                </div>
                <div class="salary-tier">
                  <span class="level">Senior</span>
                  <span class="amount">${companyData.salary_senior || '₹30L - ₹50L+'}</span>
                </div>
              </div>
            </section>
            
            <div class="gap-summary">
              <h3>Skill Gap Analysis for ${analysis.title}</h3>
              <div class="match-score">
                <span class="score-label">Match Confidence</span>
                <span class="score-value">${gapData.confidence_score || 65}%</span>
              </div>
              
              <div class="gap-category critical">
                <h4>🔴 Critical Gaps (${gapData.critical_gaps || 0})</h4>
                <ul>
                  ${(gapData.gaps?.critical || []).map(gap => `
                    <li>
                      <strong>${gap.skill_name}</strong> - Required: ${gap.required_level}, You: ${gap.current_level}
                      <span class="learning-time">~${gap.learning_time_estimate}h to learn</span>
                    </li>
                  `).join('')}
                </ul>
              </div>
              
              <div class="gap-category high">
                <h4>🟡 High Priority Gaps (${gapData.high_priority_gaps || 0})</h4>
                <ul>
                  ${(gapData.gaps?.high || []).map(gap => `
                    <li>
                      <strong>${gap.skill_name}</strong> - Required: ${gap.required_level}, You: ${gap.current_level}
                      <span class="learning-time">~${gap.learning_time_estimate}h to learn</span>
                    </li>
                  `).join('')}
                </ul>
              </div>
            </div>
            
            <div class="roadmap">
              <h3>Learning Roadmap (${gapData.estimated_weeks || 6} weeks, ${gapData.total_learning_hours || 0} hours)</h3>
              ${(roadmapData.phases || []).map(phase => `
                <div class="week">
                  <h4>${phase.title}</h4>
                  <p class="phase-duration">${phase.duration_weeks} weeks • ${phase.daily_time_estimate}h/day</p>
                  <p class="phase-focus"><strong>Focus:</strong> ${phase.focus}</p>
                  <ul>
                    ${phase.skills.map(skill => `<li>${skill}</li>`).join('')}
                  </ul>
                  <p class="phase-goals"><strong>Goals:</strong> ${phase.goals.join(', ')}</p>
                </div>
              `).join('')}
            </div>
          </div>
        `;
      } catch (error) {
        content.innerHTML = `
          <div class="company-section">
            <h2>Company & Gap Analysis</h2>
            <p class="error">Failed to load data: ${error.message}</p>
          </div>
        `;
      }
    });
  }

  // ---------- Coding Tab (Phase 6) ----------
  async function renderCodingTab() {
    content.innerHTML = '<p class="loading">Loading coding stats...</p>';

    try {
      const response = await fetch(`http://127.0.0.1:8000/coding-session/user/${currentUserId}/stats`);
      const stats = await response.json();

      if (stats.total_sessions === 0) {
        content.innerHTML = `
          <div class="coding-section">
            <h2>Coding Practice</h2>
            <p class="muted">No coding sessions logged yet.</p>
            
            <div class="session-timer">
              <h3>Start a Session</h3>
              <input type="text" id="session-problem" placeholder="Problem link or title" style="width: 100%; margin-bottom: 0.5rem;">
              <select id="session-platform" style="width: 100%; margin-bottom: 0.5rem;">
                <option value="leetcode">LeetCode</option>
                <option value="gfg">GeeksforGeeks</option>
                <option value="codeforces">Codeforces</option>
              </select>
              <button id="btn-log-session" class="btn">Log Session</button>
            </div>
            
            <div class="platform-info">
              <h4>Platform Sync</h4>
              <button id="btn-sync-leetcode" class="btn">Sync LeetCode</button>
              <button id="btn-sync-gfg" class="btn">Sync GFG</button>
              <button id="btn-sync-codeforces" class="btn">Sync Codeforces</button>
            </div>
          </div>
        `;
        bindCodingButtons();
        return;
      }

      const topicResponse = await fetch(`http://127.0.0.1:8000/coding-session/user/${currentUserId}/topic-stats`);
      const topicStats = await topicResponse.json();

      content.innerHTML = `
        <div class="coding-section">
          <h2>Coding Practice</h2>
          
          <div class="stats-overview">
            <div class="stat-card">
              <span class="stat-number">${stats.total_problems}</span>
              <span class="stat-label">Problems</span>
            </div>
            <div class="stat-card">
              <span class="stat-number">${stats.total_solved}</span>
              <span class="stat-label">Solved</span>
            </div>
            <div class="stat-card">
              <span class="stat-number">${stats.accuracy}%</span>
              <span class="stat-label">Accuracy</span>
            </div>
            <div class="stat-card">
              <span class="stat-number">${stats.streak}</span>
              <span class="stat-label">Day Streak</span>
            </div>
          </div>
          
          <div class="session-timer">
            <h3>Log New Session</h3>
            <input type="text" id="session-problem" placeholder="Problem link or title" style="width: 100%; margin-bottom: 0.5rem;">
            <select id="session-platform" style="width: 100%; margin-bottom: 0.5rem;">
              <option value="leetcode">LeetCode</option>
              <option value="gfg">GeeksforGeeks</option>
              <option value="codeforces">Codeforces</option>
            </select>
            <input type="number" id="session-duration" placeholder="Duration (minutes)" style="width: 100%; margin-bottom: 0.5rem;">
            <button id="btn-log-session" class="btn">Log Session</button>
          </div>
          
          <div class="topics-breakdown">
            <h4>Topic-wise Performance</h4>
            ${Object.entries(topicStats.topic_stats || {}).map(([topic, data]) => `
              <div class="topic-row">
                <span class="topic-name">${topic}</span>
                <span class="topic-stats">${data.solved}/${data.attempted} (${data.proficiency}%)</span>
              </div>
            `).join('')}
          </div>
          
          <div class="platform-stats">
            <h4>Platform Breakdown</h4>
            ${Object.entries(stats.problems_by_platform || {}).map(([platform, count]) => `
              <div class="platform-row">
                <span class="platform-name">${platform}</span>
                <span class="platform-count">${count} problems</span>
              </div>
            `).join('')}
          </div>
        </div>
      `;
      bindCodingButtons();
    } catch (error) {
      content.innerHTML = `
        <div class="coding-section">
          <h2>Coding Practice</h2>
          <p class="error">Failed to load coding stats: ${error.message}</p>
        </div>
      `;
    }
  }

  function bindCodingButtons() {
    document.getElementById('btn-log-session')?.addEventListener('click', async () => {
      const problem = document.getElementById('session-problem').value;
      const platform = document.getElementById('session-platform').value;
      const duration = document.getElementById('session-duration')?.value || 30;

      if (!problem) {
        alert('Please enter a problem name or link');
        return;
      }

      try {
        await fetch('http://127.0.0.1:8000/coding-session/session/log', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_id: currentUserId,
            platform: platform,
            problems_solved: [{
              platform: platform,
              problem_id: 'manual',
              problem_name: problem,
              topic: 'general',
              difficulty: 'medium',
              status: 'accepted',
              solve_time_minutes: parseInt(duration)
            }],
            session_duration_minutes: parseInt(duration),
            session_type: 'practice'
          })
        });
        renderCodingTab();
      } catch (error) {
        alert('Failed to log session: ' + error.message);
      }
    });

    document.getElementById('btn-sync-leetcode')?.addEventListener('click', async () => {
      chrome.storage.local.get('userSettings', async (data) => {
        const username = data.userSettings?.leetcode_username;
        if (!username) {
          alert('Please set your LeetCode username in Settings first');
          return;
        }

        try {
          const response = await fetch('http://127.0.0.1:8000/coding-session/sync/leetcode', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              user_id: currentUserId,
              username: username
            })
          });
          const result = await response.json();
          
          if (result.ok) {
            alert(`Synced LeetCode profile: ${result.total_solved} problems solved (E: ${result.easy}, M: ${result.medium}, H: ${result.hard})`);
            renderCodingTab();
          } else {
            alert('Sync failed: ' + (result.error || result.message));
          }
        } catch (error) {
          alert('Failed to sync LeetCode: ' + error.message);
        }
      });
    });

    document.getElementById('btn-sync-gfg')?.addEventListener('click', async () => {
      chrome.storage.local.get('userSettings', async (data) => {
        const username = data.userSettings?.gfg_username;
        if (!username) {
          alert('Please set your GFG username in Settings first');
          return;
        }

        try {
          const response = await fetch('http://127.0.0.1:8000/coding-session/sync/gfg', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              user_id: currentUserId,
              username: username
            })
          });
          const result = await response.json();
          
          if (result.ok) {
            alert(`Synced GFG profile: ${result.problems_solved} problems solved, Coding Score: ${result.coding_score}`);
            renderCodingTab();
          } else {
            alert('Sync failed: ' + (result.error || result.message));
          }
        } catch (error) {
          alert('Failed to sync GFG: ' + error.message);
        }
      });
    });

    document.getElementById('btn-sync-codeforces')?.addEventListener('click', async () => {
      chrome.storage.local.get('userSettings', async (data) => {
        const username = data.userSettings?.codeforces_username;
        if (!username) {
          alert('Please set your Codeforces username in Settings first');
          return;
        }

        try {
          const response = await fetch('http://127.0.0.1:8000/coding-session/sync/codeforces', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              user_id: currentUserId,
              username: username
            })
          });
          const result = await response.json();
          
          if (result.ok) {
            alert(`Synced Codeforces profile: Rating ${result.rating}, Max: ${result.max_rating}, ${result.total_problems_solved} problems solved`);
            renderCodingTab();
          } else {
            alert('Sync failed: ' + (result.error || result.message));
          }
        } catch (error) {
          alert('Failed to sync Codeforces: ' + error.message);
        }
      });
    });
  }

  // ---------- Applications Tab (Auto-update only) ----------
  async function renderApplicationsTab() {
    content.innerHTML = '<p class="loading">Loading applications (auto-synced)...';

    try {
      const [appsResponse, analyticsResponse, pipelineResponse] = await Promise.all([
        fetch(`http://127.0.0.1:8000/applications/user/${currentUserId}/applications`),
        fetch(`http://127.0.0.1:8000/applications/user/${currentUserId}/analytics`),
        fetch(`http://127.0.0.1:8000/applications/user/${currentUserId}/pipeline`)
      ]);

      const apps = await appsResponse.json();
      const analytics = await analyticsResponse.json();
      const pipeline = await pipelineResponse.json();

      content.innerHTML = `
        <div class="applications">
          <h2>📋 Application Tracking</h2>
          <p class="muted">Applications are auto-synced from your job analysis history</p>
          
          <div class="pipeline-chart">
            <div class="stage applied">
              <span class="count">${pipeline.pipeline?.applied?.length || 0}</span>
              <span class="label">Applied</span>
            </div>
            <div class="arrow">→</div>
            <div class="stage shortlisted">
              <span class="count">${pipeline.pipeline?.shortlisted?.length || 0}</span>
              <span class="label">Shortlisted</span>
            </div>
            <div class="arrow">→</div>
            <div class="stage interviewed">
              <span class="count">${pipeline.pipeline?.interviewed?.length || 0}</span>
              <span class="label">Interview</span>
            </div>
            <div class="arrow">→</div>
            <div class="stage offered">
              <span class="count">${pipeline.pipeline?.offered?.length || 0}</span>
              <span class="label">Offer</span>
            </div>
          </div>
          
          <div class="applications-list">
            <h3>Recent Applications</h3>
            ${(apps.applications || []).slice(0, 10).map(app => `
              <div class="application-card">
                <div class="status ${app.status}">${app.status}</div>
                <div class="details">
                  <h4>${app.job_title}</h4>
                  <p class="company">${app.company}</p>
                  <p class="date">Applied: ${new Date(app.application_date).toLocaleDateString()}</p>
                  ${app.interview_date ? `<p class="interview-date">Interview: ${new Date(app.interview_date).toLocaleDateString()}</p>` : ''}
                  ${app.match_score ? `<p class="match-score">Match: ${app.match_score}%</p>` : ''}
                </div>
                <div class="actions">
                  <select onchange="updateApplicationStatus(${app.id}, this.value)">
                    <option value="applied" ${app.status === 'applied' ? 'selected' : ''}>Applied</option>
                    <option value="shortlisted" ${app.status === 'shortlisted' ? 'selected' : ''}>Shortlisted</option>
                    <option value="interviewed" ${app.status === 'interviewed' ? 'selected' : ''}>Interview</option>
                    <option value="offered" ${app.status === 'offered' ? 'selected' : ''}>Offer</option>
                    <option value="rejected" ${app.status === 'rejected' ? 'selected' : ''}>Rejected</option>
                  </select>
                </div>
              </div>
            `).join('')}
          </div>
          
          <div class="analytics">
            <h3>📊 Statistics</h3>
            <div class="stats-grid">
              <div class="stat">
                <span class="number">${analytics.total_applications || 0}</span>
                <span class="label">Total Applications</span>
              </div>
              <div class="stat">
                <span class="number">${analytics.success_rate || 0}%</span>
                <span class="label">Success Rate</span>
              </div>
              <div class="stat">
                <span class="number">${analytics.interview_stage_count || 0}</span>
                <span class="label">Interviews</span>
              </div>
              <div class="stat">
                <span class="number">${analytics.offers || 0}</span>
                <span class="label">Offers</span>
              </div>
            </div>
          </div>
        </div>
      `;
    } catch (error) {
      content.innerHTML = `
        <div class="applications">
          <h2>📋 Application Tracking</h2>
          <p class="error">Failed to load applications: ${error.message}</p>
        </div>
      `;
    }
  }

  window.updateApplicationStatus = async (appId, newStatus) => {
    try {
      await fetch(`http://127.0.0.1:8000/applications/update/${appId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: currentUserId,
          application_id: appId,
          new_status: newStatus
        })
      });
      renderApplicationsTab();
    } catch (error) {
      alert('Failed to update status: ' + error.message);
    }
  };

  // ---------- Settings Tab ----------
  async function renderSettingsTab() {
    chrome.storage.local.get(['userSettings'], (data) => {
      const settings = data.userSettings || {
        resume_url: '',
        github_username: '',
        leetcode_username: '',
        gfg_username: '',
        codeforces_username: ''
      };

      content.innerHTML = `
        <div class="settings-section">
          <h2>⚙️ Settings</h2>
          
          <div class="settings-group">
            <h3>Profile</h3>
            <div class="setting-item">
              <label>Resume URL (Google Drive, etc.)</label>
              <input type="url" id="setting-resume" value="${settings.resume_url || ''}" placeholder="https://docs.google.com/document/..." style="width: 100%; padding: 8px; border: 1px solid #d1d5db; border-radius: 4px;">
            </div>
          </div>
          
          <div class="settings-group">
            <h3>Coding Platforms</h3>
            <div class="setting-item">
              <label>GitHub Username</label>
              <div style="display: flex; gap: 8px;">
                <input type="text" id="setting-github" value="${settings.github_username || ''}" placeholder="your-username" style="flex: 1; padding: 8px; border: 1px solid #d1d5db; border-radius: 4px;">
                <button id="btn-sync-github" class="btn" style="margin: 0;">Sync</button>
              </div>
            </div>
            <div class="setting-item">
              <label>LeetCode Username</label>
              <input type="text" id="setting-leetcode" value="${settings.leetcode_username || ''}" placeholder="your-username" style="width: 100%; padding: 8px; border: 1px solid #d1d5db; border-radius: 4px;">
            </div>
            <div class="setting-item">
              <label>GeeksforGeeks Username</label>
              <input type="text" id="setting-gfg" value="${settings.gfg_username || ''}" placeholder="your-username" style="width: 100%; padding: 8px; border: 1px solid #d1d5db; border-radius: 4px;">
            </div>
            <div class="setting-item">
              <label>Codeforces Username</label>
              <input type="text" id="setting-codeforces" value="${settings.codeforces_username || ''}" placeholder="your-username" style="width: 100%; padding: 8px; border: 1px solid #d1d5db; border-radius: 4px;">
            </div>
          </div>
          
          <button id="btn-save-settings" class="btn">Save Settings</button>
          <p class="muted" style="margin-top: 8px;">These settings will be used to sync your coding stats and profile data.</p>
        </div>
      `;

      document.getElementById('btn-save-settings')?.addEventListener('click', () => {
        const newSettings = {
          resume_url: document.getElementById('setting-resume').value,
          github_username: document.getElementById('setting-github').value,
          leetcode_username: document.getElementById('setting-leetcode').value,
          gfg_username: document.getElementById('setting-gfg').value,
          codeforces_username: document.getElementById('setting-codeforces').value
        };
        chrome.storage.local.set({ userSettings: newSettings }, () => {
          alert('Settings saved successfully!');
        });
      });

      document.getElementById('btn-sync-github')?.addEventListener('click', async () => {
        const username = document.getElementById('setting-github').value;
        if (!username) {
          alert('Please enter a GitHub username first');
          return;
        }

        try {
          const response = await fetch(`http://127.0.0.1:8000/github/profile/${username}`);
          const result = await response.json();
          
          if (result.error) {
            alert('GitHub sync failed: ' + result.error);
          } else {
            alert(`GitHub profile synced: ${result.public_repos} repos, ${result.followers} followers`);
          }
        } catch (error) {
          alert('Failed to sync GitHub: ' + error.message);
        }
      });
    });
  }

  // ---------- Tab Rendering ----------
  function renderActiveTab() {
    switch (activeTab) {
      case 'Job':
        chrome.storage.local.get('lastJobAnalysis', (data) => {
          renderJobTab(data.lastJobAnalysis || null, null);
        });
        break;
      case 'Company':
        renderCompanyTab();
        break;
      case 'Coding':
        renderCodingTab();
        break;
      case 'Applications':
        renderApplicationsTab();
        break;
      case 'Settings':
        renderSettingsTab();
        break;
      default:
        content.innerHTML = '<p>Select a tab to view details.</p>';
    }
  }

  tabs.forEach((tab) => {
    tab.addEventListener('click', () => {
      tabs.forEach((t) => t.classList.remove('active'));
      tab.classList.add('active');
      activeTab = tab.innerText;
      renderActiveTab();
    });
  });

  tabs[0].classList.add('active');
  renderActiveTab();

  chrome.storage.onChanged.addListener((changes, area) => {
    if (area !== 'local') return;
    if (changes.lastJobAnalysis && activeTab === 'Job') {
      renderJobTab(changes.lastJobAnalysis.newValue, null);
    }
  });

  fetch('http://127.0.0.1:8000/health')
    .then((res) => res.json())
    .then((data) => {
      statusEl.textContent = `Backend: ${data.status}, DB: ${data.database}`;
    })
    .catch(() => {
      statusEl.textContent = 'Backend: offline — run scripts/start-backend.ps1';
    });
});
