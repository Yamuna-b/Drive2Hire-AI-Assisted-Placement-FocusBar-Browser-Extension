document.addEventListener('DOMContentLoaded', () => {
  const content = document.getElementById('content');
  const statusEl = document.getElementById('backend-status');
  const tabs = document.querySelectorAll('nav ul li');
  let activeTab = 'Job';

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

    // Enable/disable fields based on Yes/No selection
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
      // Update chrome.storage.local userSkills
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
      // Trigger re‑analysis to refresh UI
      chrome.runtime.sendMessage({ type: 'analyseCurrentTab' }, () => {});
    });
  }

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
    
    // Bind Q&A button
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
      
      // Call backend to generate Q&A questions
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

  function renderPlaceholder(label) {
    const messages = {
      Company: [
        'Company tab (Phase 5)',
        'Will show company type, industry, tech stack, and roles.',
        'Data source to be confirmed before implementation.',
      ],
      Coding: [
        'Coding tab (Phase 6)',
        'Will show session timer and topic-wise stats.',
        'LeetCode / GFG / Codeforces parsing comes next.',
      ],
    };
    const lines = messages[label] || ['No content yet.'];
    content.innerHTML = lines.map((line) => `<p>${line}</p>`).join('');
  }

  function renderActiveTab() {
    if (activeTab === 'Job') {
      chrome.storage.local.get('lastJobAnalysis', (data) => {
        renderJobTab(data.lastJobAnalysis || null, null);
      });
      return;
    }
    renderPlaceholder(activeTab);
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
    if (area !== 'local' || activeTab !== 'Job') return;
    if (changes.lastJobAnalysis) {
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
