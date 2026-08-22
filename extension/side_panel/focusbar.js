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

  function renderJobTab(analysis, error) {
    if (error) {
      content.innerHTML = `
        <p class="error">${error}</p>
        <button id="btn-analyse" class="btn">Analyze current job page</button>
        <p class="muted">Open a LinkedIn or Naukri job listing first.</p>
      `;
      bindAnalyseButton();
      return;
    }

    if (!analysis) {
      content.innerHTML = `
        <p>No job analyzed yet.</p>
        <button id="btn-analyse" class="btn">Analyze current job page</button>
        <p class="muted">Visit a LinkedIn or Naukri job page, then click above.</p>
      `;
      bindAnalyseButton();
      return;
    }

    const match = analysis.match || { covered: [], weak: [], missing: [] };

    content.innerHTML = `
      <div class="job-snapshot">
        <h2>${analysis.title || 'Unknown role'}</h2>
        <p class="company">${analysis.company || 'Unknown company'}</p>
      </div>

      ${skillList('Mandatory skills', analysis.mandatory_skills, 'mandatory')}
      ${skillList('Nice-to-have skills', analysis.nice_to_have_skills, 'nice')}

      <div class="match-section">
        <strong>Your match</strong>
        ${skillList('Covered', match.covered, 'covered')}
        ${skillList('Weak', match.weak, 'weak')}
        ${skillList('Missing', match.missing, 'missing')}
      </div>

      <button id="btn-analyse" class="btn">Re-analyze current page</button>
    `;
    bindAnalyseButton();
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
              const msg =
                response?.error ||
                chrome.runtime.lastError?.message ||
                'Analysis failed. Is the backend running?';
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
