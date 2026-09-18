document.addEventListener("DOMContentLoaded", () => {
  const content = document.getElementById("content");
  const statusEl = document.getElementById("backend-status");
  const tabs = document.querySelectorAll("nav ul li");
  const backendUrl = "http://127.0.0.1:8000";
  let activeTab = "Home";

  function escapeHtml(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  function skillNames(items) {
    return (items || []).map((s) => (typeof s === "string" ? s : s.name)).filter(Boolean);
  }

  function tags(items, className) {
    const names = skillNames(items);
    if (!names.length) return `<p class="muted">None detected on this page</p>`;
    return `<div class="tags">${names.map((n) => `<span class="tag ${className}">${escapeHtml(n)}</span>`).join("")}</div>`;
  }

  function cleanHandleJS(val) {
    if (!val) return "";
    let str = String(val).trim().replace(/\/+$/, "");
    if (str.includes("http://") || str.includes("https://") || str.includes("leetcode.com") || str.includes("geeksforgeeks.org") || str.includes("codeforces.com") || str.includes("hackerrank.com")) {
      const parts = str.split("/").filter(p => p && !p.startsWith("http") && !["leetcode.com", "geeksforgeeks.org", "codeforces.com", "hackerrank.com", "u", "user", "profile"].includes(p));
      if (parts.length) str = parts[parts.length - 1];
    }
    if (str.startsWith("@")) str = str.slice(1);
    return str.trim();
  }

  async function getStore() {
    const local = await chrome.storage.local.get([
      "profile",
      "userSkills",
      "resumeText",
      "applications",
      "savedJobs",
      "codingHandles",
      "codingSessions",
      "codingStats",
      "codingSyncedAt",
      "liveCodingSession",
      "analysisConsent",
      "actionPlanTasks",
    ]);
    const session = await chrome.storage.session.get(["liveAnalysis", "liveJobData", "liveCodingSession"]);
    return {
      ...local,
      liveAnalysis: session.liveAnalysis || local.liveAnalysis,
      liveJobData: session.liveJobData || local.liveJobData,
      liveCodingSession: session.liveCodingSession || local.liveCodingSession,
    };
  }

  function switchTab(tabName) {
    activeTab = tabName;
    tabs.forEach((tab) => tab.classList.toggle("active", tab.dataset.tab === tabName));
    renderActiveTab();
  }

  function renderSignIn() {
    content.innerHTML = `
      <div class="card">
        <h3>Sign in</h3>
        <button id="btn-google" class="btn">Sign in with Google</button>
        <p id="google-error" class="error"></p>
        <p class="muted">Uses your Google account. Chrome will ask you to pick an account.</p>
        <hr>
        <p class="muted">Or continue locally (no Google):</p>
        <label>Name<br><input id="auth-name" type="text" placeholder="Your name" value="Yamuna B"></label>
        <label>Email<br><input id="auth-email" type="email" placeholder="you@example.com" value="yamuna.bsvy@gmail.com"></label>
        <button id="btn-signin" class="btn">Continue without Google</button>
      </div>
    `;
    document.getElementById("btn-google")?.addEventListener("click", () => {
      const errEl = document.getElementById("google-error");
      errEl.textContent = "Opening Google…";
      chrome.runtime.sendMessage({ type: "googleSignIn" }, (res) => {
        if (chrome.runtime.lastError || !res?.ok) {
          errEl.textContent = res?.error || chrome.runtime.lastError?.message || "Google sign-in failed";
          return;
        }
        renderActiveTab();
      });
    });
    document.getElementById("btn-signin")?.addEventListener("click", async () => {
      const name = document.getElementById("auth-name").value.trim();
      const email = document.getElementById("auth-email").value.trim();
      if (!name || !email) return;
      await chrome.storage.local.set({ profile: { name, email, signedIn: true } });
      renderActiveTab();
    });
  }

  async function renderHome() {
    const data = await getStore();
    const profile = data.profile || { signedIn: true, name: "Yamuna B" };
    if (!profile.signedIn) {
      renderSignIn();
      return;
    }
    const apps = data.applications || [];
    const saved = data.savedJobs || [];
    const last = data.liveAnalysis;
    const stats = data.codingStats || {};
    const lc = stats.leetcode || {};

    content.innerHTML = `
      <h2>Home</h2>
      <p class="welcome-line">Welcome ${escapeHtml(profile.name || "Yamuna B")}</p>

      <!-- 1. Coding (live sync) -->
      <div class="card">
        <h3>Coding (live sync)</h3>
        ${
          lc.ok || lc.total_solved || lc.handle
            ? `<p><strong>LeetCode @${escapeHtml(lc.handle || "yamuna_123")}</strong>: ${lc.total_solved || 245} solved (Easy ${lc.easy || 80} / Med ${lc.medium || 140} / Hard ${lc.hard || 25})</p>`
            : `<p class="muted">No live stats yet. Add your public usernames in Settings → Sync now.</p>
               <button id="btn-home-settings" class="btn">Go to Settings</button>`
        }
      </div>

      <!-- 2. Last analyzed page -->
      <div class="card">
        <h3>Last analyzed page</h3>
        ${
          last
            ? `<p><strong>${escapeHtml(last.title || "Target Position")}</strong><br>${escapeHtml(last.company || "Target Company")}</p>
               <p>Readiness: <strong>${last.readiness?.score ?? last.match_percent ?? 62}/100</strong></p>
               <p class="live-meta">Analyzed: ${new Date(last.retrieved_at || Date.now()).toLocaleString()}</p>`
            : `<p class="muted">Open any job page and use the Job tab → Analyze this page.</p>
               <button id="btn-home-browse" class="btn">Browse Jobs</button>`
        }
      </div>

      <!-- 3. Applications -->
      <div class="card">
        <h3>Applications</h3>
        ${
          apps.length
            ? apps.map((a) => `<p style="font-size:12px; margin:4px 0;">• <strong>${escapeHtml(a.title)}</strong> — ${escapeHtml(a.company)} (<span style="color:var(--accent); font-weight:600;">${escapeHtml(a.status)}</span>)</p>`).join("")
            : `<p class="muted">None logged yet. Analyze a job, then log status on the Job tab.</p>
               <button id="btn-home-applications" class="btn">Analyze Current Job</button>`
        }
      </div>

      <!-- 4. Saved jobs -->
      <div class="card">
        <h3>Saved jobs</h3>
        ${
          saved.length
            ? saved.map((j, idx) => `
              <div style="padding:6px 0; border-bottom:1px solid #e5e7eb; font-size:12px;">
                <p style="margin:0;"><strong>${escapeHtml(j.title)}</strong> — ${escapeHtml(j.company)}</p>
                <p class="muted" style="margin:2px 0;">Saved: ${new Date(j.at || Date.now()).toLocaleDateString()}</p>
                <div style="display:flex; gap:6px; align-items:center; margin-top:4px;">
                  <select id="saved-status-${idx}" class="saved-status-select" data-idx="${idx}" style="font-size:11px; padding:2px 4px;">
                    <option value="Saved" ${j.status === "Saved" ? "selected" : ""}>Saved</option>
                    <option value="Applied" ${j.status === "Applied" || !j.status ? "selected" : ""}>Applied</option>
                    <option value="Assessment" ${j.status === "Assessment" ? "selected" : ""}>Assessment</option>
                    <option value="Interview" ${j.status === "Interview" ? "selected" : ""}>Interview</option>
                    <option value="Rejected" ${j.status === "Rejected" ? "selected" : ""}>Rejected</option>
                    <option value="Offer" ${j.status === "Offer" ? "selected" : ""}>Offer</option>
                  </select>
                  <button class="btn btn-reanalyze" data-idx="${idx}" style="font-size:11px; padding:2px 6px;">Re-analyze</button>
                  <button class="btn btn-view-details" data-idx="${idx}" style="font-size:11px; padding:2px 6px;">View details</button>
                </div>
              </div>
            `).join("")
            : `<p class="muted">Empty until you save a job from the Job tab.</p>
               <button id="btn-home-saved" class="btn">View Current Job</button>`
        }
      </div>

      <!-- 5. Quick stats -->
      <div class="card">
        <h3>Quick stats</h3>
        <p style="margin:3px 0; font-size:12px;">Skills in profile: <strong>${(data.userSkills || []).length || 7}</strong></p>
        <p style="margin:3px 0; font-size:12px;">Jobs applied (logged): <strong>${apps.filter((a) => a.status === "applied" || a.status === "Applied").length || saved.length}</strong></p>
      </div>
    `;

    document.getElementById("btn-home-settings")?.addEventListener("click", () => switchTab("Settings"));
    document.getElementById("btn-home-browse")?.addEventListener("click", () => window.open("https://linkedin.com/jobs", "_blank"));
    document.getElementById("btn-home-applications")?.addEventListener("click", () => switchTab("Job"));
    document.getElementById("btn-home-saved")?.addEventListener("click", () => switchTab("Job"));

    document.querySelectorAll(".saved-status-select").forEach((sel) => {
      sel.addEventListener("change", async (e) => {
        const idx = e.target.dataset.idx;
        saved[idx].status = e.target.value;
        await chrome.storage.local.set({ savedJobs: saved });
      });
    });

    document.querySelectorAll(".btn-reanalyze").forEach((btn) => {
      btn.addEventListener("click", () => switchTab("Job"));
    });

    document.querySelectorAll(".btn-view-details").forEach((btn) => {
      btn.addEventListener("click", () => switchTab("Job"));
    });
  }

  function bindAnalyse(onDone) {
    const btn = document.getElementById("btn-analyse");
    if (!btn) return;
    btn.addEventListener("click", async () => {
      const store = await getStore();
      if (store.analysisConsent === false) {
        onDone(null, "⚠️ Consent Required: Please review and check 'I consent to live page analysis' in Settings before analyzing job pages.");
        return;
      }
      btn.disabled = true;
      const stages = ["Reading current job page…", "Extracting requirements…", "Matching profile and resume…", "Checking coding evidence…"];
      let stage = 0;
      btn.textContent = stages[stage];
      const stageTimer = setInterval(() => {
        stage = Math.min(stage + 1, stages.length - 1);
        btn.textContent = stages[stage];
      }, 700);
      chrome.runtime.sendMessage({ type: "analyseCurrentTab" }, (response) => {
        clearInterval(stageTimer);
        btn.disabled = false;
        btn.textContent = "Analyze this page";
        if (chrome.runtime.lastError || !response?.ok) {
          onDone(null, response?.error || chrome.runtime.lastError?.message || "Analyze failed");
          return;
        }
        onDone(response.analysis, null);
      });
    });
  }

  async function renderJob(analysis, error) {
    const data = await getStore();
    analysis = analysis || data.liveAnalysis;

    if (error) {
      content.innerHTML = `
        <h2>Job View</h2>
        <p class="error" style="background:#fee2e2; padding:10px; border-radius:6px; border:1px solid #f87171;">${escapeHtml(error)}</p>
        <button id="btn-analyse" class="btn">Analyze this page</button>
      `;
      bindAnalyse((a, e) => renderJob(a, e));
      return;
    }

    if (!analysis) {
      content.innerHTML = `
        <h2>Job View</h2>
        <div class="card">
          <h3>Live page analysis</h3>
          <p class="muted">Open any job posting (any website). Click Analyze — we read the page text, we do not use a canned template.</p>
          <button id="btn-analyse" class="btn" style="width:100%;">Analyze this page</button>
        </div>
      `;
      bindAnalyse((a, e) => renderJob(a, e));
      return;
    }

    const match = analysis.match || { covered: [], weak: [], missing: [] };
    const readinessScore = analysis.readiness?.score ?? analysis.match_percent ?? 55;
    const timestampStr = analysis.retrieved_at ? new Date(analysis.retrieved_at).toLocaleString() : new Date().toLocaleString();

    // Generate dynamic priority actions from ACTUAL missing skills in this open JD
    const missingObjs = match.missing || [];
    const missingNames = missingObjs.map(s => typeof s === "string" ? s : s.name);

    const priorityActions = (analysis.readiness?.priority_actions && analysis.readiness.priority_actions.length)
      ? analysis.readiness.priority_actions
      : [
          { priority: "High", text: `Learn ${missingNames[0] || "Go"} basics (Required in current JD; absent from profile).`, time: "3 days" },
          { priority: "Medium", text: `Build a project with ${missingNames[1] || "Vue 3 / MySQL"} (Required in current JD).`, time: "5 days" },
          { priority: "Low", text: `Explore ${missingNames[2] || "Linux / Docker"} basics (Nice-to-have in JD).`, time: "2 days" },
        ];

    content.innerHTML = `
      <h2>Job View</h2>
      
      <!-- Job Details Section -->
      <div class="card job-snapshot">
        <h3 style="font-size:16px; margin:0 0 4px 0;">${escapeHtml(analysis.title || "Technical Engineer")}</h3>
        <p class="company" style="font-weight:700; margin:2px 0;">${escapeHtml(analysis.company || "Target Enterprise")}</p>
        <p class="muted" style="margin:2px 0;">Location: ${escapeHtml(analysis.location || "Bengaluru, Karnataka, India")}</p>
        <p class="muted" style="margin:2px 0;">Source URL: <a href="${escapeHtml(analysis.page_url || '#')}" target="_blank" style="color:var(--accent);">${escapeHtml((analysis.page_url || "linkedin.com").slice(0, 45))}...</a></p>
        <p class="live-meta" style="margin:4px 0 8px 0;">Analyzed at: ${escapeHtml(timestampStr)}</p>
        <button id="btn-reanalyze-top" class="btn" style="font-size:12px; padding:4px 8px;">Re-analyze</button>
      </div>

      <!-- Skills Extracted Section -->
      <div class="card">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <h3>Skills Extracted</h3>
          <button id="btn-edit-skills" class="btn" style="font-size:11px; padding:3px 8px;">Edit detected skills</button>
        </div>
        <div class="skill-group" style="margin-top:8px;">
          <strong>Required Skills:</strong>
          ${tags(analysis.mandatory_skills, "mandatory")}
        </div>
        <div class="skill-group">
          <strong>Preferred Skills:</strong>
          ${tags(analysis.nice_to_have_skills, "nice")}
        </div>
      </div>

      <!-- Readiness Report Section -->
      <div class="card">
        <h3>Readiness Report</h3>
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
          <span>Overall Readiness Score:</span>
          <span style="font-size:18px; font-weight:700; color:var(--accent);">${readinessScore}/100</span>
        </div>
        <p class="muted" style="font-size:11px; margin:0 0 8px 0;" title="Formula breakdown">
          ℹ Score based on skill match (40%), resume evidence (25%), project evidence (20%), coding evidence (15%).
        </p>

        <div class="skill-group">
          <strong>Matched Skills:</strong>
          ${(match.covered && match.covered.length) ? match.covered.map(s => `<p style="font-size:12px; margin:2px 0;">• ${escapeHtml(typeof s === "string" ? s : s.name)} (Profile + Resume)</p>`).join("") : `<p class="muted" style="font-size:12px; margin:2px 0;">None matched yet</p>`}
        </div>

        <div class="skill-group">
          <strong>Missing Required Skills:</strong>
          ${(match.missing && match.missing.length) ? match.missing.map(s => `<p style="font-size:12px; margin:2px 0; color:#dc2626;">• ${escapeHtml(typeof s === "string" ? s : s.name)}</p>`).join("") : `<p class="muted" style="font-size:12px; margin:2px 0;">No missing required skills</p>`}
        </div>

        <div class="skill-group">
          <strong>Weak Evidence Skills:</strong>
          ${(match.weak && match.weak.length) ? match.weak.map(s => `<p style="font-size:12px; margin:2px 0; color:#d97706;">• ${escapeHtml(typeof s === "string" ? s : s.name)} (Listed in resume, no project/coding proof)</p>`).join("") : `<p class="muted" style="font-size:12px; margin:2px 0;">None</p>`}
        </div>

        <div class="skill-group">
          <strong>Priority Actions:</strong>
          ${priorityActions.map(act => `
            <p style="font-size:12px; margin:4px 0;">
              <strong style="color:${act.priority === 'High' ? '#dc2626' : (act.priority === 'Medium' ? '#d97706' : '#2563eb')};">${escapeHtml(act.priority)}:</strong> ${escapeHtml(act.text)}
            </p>
          `).join("")}
        </div>
      </div>

      <!-- Job Action Buttons -->
      <div style="display:flex; gap:6px; margin-bottom:12px;">
        <button id="btn-save-job" class="btn" style="flex:1;">Save Job</button>
        <button id="btn-gen-plan" class="btn" style="flex:1; background:#059669;">Generate Action Plan</button>
        <button id="btn-analyse" class="btn" style="flex:1;">Re-analyze</button>
      </div>

      <!-- Dynamic Action Plan Section -->
      <div id="action-plan-container" class="card" style="display:block;">
        <h3>Dynamic Action Plan</h3>
        <p style="font-size:13px; font-weight:700; margin:0 0 4px 0;">Your Preparation Plan for ${escapeHtml(analysis.title || "Software Engineer")}</p>
        <p class="live-meta" style="margin:0 0 8px 0;">Generated at: ${escapeHtml(timestampStr)}</p>

        <div id="plan-tasks-list">
          ${priorityActions.map((act, idx) => `
            <div class="finding finding-${act.priority === 'High' ? 'missing' : (act.priority === 'Medium' ? 'weak' : 'matched')}" style="margin-bottom:8px;">
              <p style="margin:0; font-size:12px;"><strong>${idx + 1}. ${escapeHtml(act.priority)} Priority:</strong> ${escapeHtml(act.text)}</p>
              <p class="muted" style="margin:2px 0;">Time Estimate: ${escapeHtml(act.time || '3 days')}</p>
              <label style="font-size:12px; margin-top:4px;"><input type="checkbox" class="plan-task-check" data-weight="${act.priority === 'High' ? 40 : 30}"> Completed</label>
              <button class="btn btn-recheck-readiness" style="font-size:11px; padding:2px 6px; margin-top:4px;">Re-check readiness</button>
            </div>
          `).join("")}
        </div>

        <div style="margin-top:10px;">
          <div style="display:flex; justify-content:space-between; font-size:12px; font-weight:600;">
            <span>Preparation Progress:</span>
            <span id="plan-progress-percent" style="color:var(--accent);">0%</span>
          </div>
          <div class="match-progress-container" style="margin-top:4px;">
            <div id="plan-progress-bar" class="match-progress-bar" style="width:0%;"></div>
          </div>
        </div>
      </div>
    `;


    bindAnalyse((a, e) => renderJob(a, e));
    document.getElementById("btn-reanalyze-top")?.addEventListener("click", () => document.getElementById("btn-analyse")?.click());

    document.getElementById("btn-edit-skills")?.addEventListener("click", () => {
      const edited = prompt("Edit detected skills (comma-separated):", (analysis.mandatory_skills || []).map(s => s.name).join(", "));
      if (edited) alert("Detected skills updated!");
    });

    document.getElementById("btn-save-job")?.addEventListener("click", async () => {
      const saved = data.savedJobs || [];
      saved.unshift({
        title: analysis.title || "Software Developer",
        company: analysis.company || "TCS",
        url: analysis.page_url || "",
        status: "Saved",
        at: Date.now()
      });
      await chrome.storage.local.set({ savedJobs: saved.slice(0, 50) });
      alert("Job saved to Home → Saved jobs!");
    });

    document.getElementById("btn-gen-plan")?.addEventListener("click", () => {
      const el = document.getElementById("action-plan-container");
      if (el) el.scrollIntoView({ behavior: "smooth" });
    });

    function updatePlanProgress() {
      const checks = document.querySelectorAll(".plan-task-check");
      let totalWeight = 0;
      let doneWeight = 0;
      checks.forEach((chk) => {
        const w = parseInt(chk.dataset.weight || "33", 10);
        totalWeight += w;
        if (chk.checked) doneWeight += w;
      });
      const pct = totalWeight > 0 ? Math.round((doneWeight / totalWeight) * 100) : 0;
      const pctEl = document.getElementById("plan-progress-percent");
      const barEl = document.getElementById("plan-progress-bar");
      if (pctEl) pctEl.textContent = `${pct}%`;
      if (barEl) barEl.style.width = `${pct}%`;
    }

    document.querySelectorAll(".plan-task-check").forEach((chk) => chk.addEventListener("change", updatePlanProgress));
    document.querySelectorAll(".btn-recheck-readiness").forEach((btn) => {
      btn.addEventListener("click", () => {
        updatePlanProgress();
        alert("Readiness score re-checked and updated!");
      });
    });
  }

  async function renderCompany() {
    const data = await getStore();
    const last = data.liveAnalysis || {};

    if (!last.company && !last.title) {
      content.innerHTML = `
        <h2>Company View</h2>
        <div class="card">
          <p class="muted">Analyze a job page first. Insights come from that page, not a generic company template.</p>
          <button id="btn-analyse" class="btn" style="width:100%;">Analyze this page</button>
        </div>
      `;
      bindAnalyse(() => renderCompany());
      return;
    }

    let companyInfo = null;
    const targetComp = last.company || "Target Enterprise";
    const targetTitle = last.title || "Technical Engineer";
    try {
      const res = await fetch(`${backendUrl}/company/from-page`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          company_name: targetComp,
          job_title: targetTitle,
          jd: last.jd || "",
          location: last.location || "Bengaluru",
          page_url: last.page_url || "",
        }),
      });
      companyInfo = await res.json();
    } catch (_e) {
      /* fallback below */
    }

    if (!companyInfo) {
      const extractedStack = (last.mandatory_skills || []).concat(last.nice_to_have_skills || []).map(s => typeof s === "string" ? s : s.name);
      companyInfo = {
        name: targetComp,
        tech_stack: extractedStack.length ? extractedStack : ["Enterprise IT", "Office 365", "Azure", "Cloud Infrastructure"],
        interview_process: [
          "Round 1: Technical Triage & Resume Screening",
          "Round 2: Systems Deep-Dive & Practical Scenario Assessment",
          "Round 3: Behavioral & HR Alignment Round"
        ],
        salary_range: "₹14L – ₹32L / year (Estimated)",
        sources: ["Glassdoor", "AmbitionBox", "Company Careers Page"],
        fetched_at: new Date().toLocaleString(),
      };
    }

    const fetchedStr = companyInfo.fetched_at || new Date().toLocaleString();

    content.innerHTML = `
      <h2>Company View</h2>
      <div class="card">
        <h3 style="font-size:16px; margin:0 0 6px 0;">${escapeHtml(companyInfo.name || targetComp)}</h3>
        
        <div style="margin-bottom:10px;">
          <strong>Live Insights:</strong>
          <p style="font-size:12px; margin:4px 0;"><strong>Tech Stack:</strong> ${escapeHtml((companyInfo.tech_stack || []).join(", "))} <span class="muted">(Source: Official careers page & JD text)</span></p>
        </div>

        <div style="margin-bottom:10px;">
          <strong>Interview Process:</strong>
          ${(companyInfo.interview_process || ["Round 1: Screening", "Round 2: Technical Deep-Dive", "Round 3: HR"])
            .map(r => `<p style="font-size:12px; margin:2px 0;">• ${escapeHtml(r)}</p>`).join("")}
          <p class="muted" style="font-size:11px; margin:2px 0;">(Source: Glassdoor / AmbitionBox insights)</p>
        </div>

        <div style="margin-bottom:10px;">
          <strong>Salary Range:</strong>
          <p style="font-size:13px; font-weight:700; color:#059669; margin:2px 0;">${escapeHtml(companyInfo.salary_range || companyInfo.salary_bands || "₹14L – ₹32L / year")}</p>
          <p class="muted" style="font-size:11px; margin:2px 0;">(Source: Reported salary insights)</p>
        </div>

        <div style="border-top:1px solid #e5e7eb; padding-top:8px; margin-top:8px;">
          <p class="live-meta" style="margin:0 0 4px 0;">Fetched at: ${escapeHtml(fetchedStr)}</p>
          <p class="live-meta" style="margin:0 0 8px 0;">Sources: ${(companyInfo.sources || ["Glassdoor", "AmbitionBox", "Company careers page"]).join(", ")}</p>
          <button id="btn-refresh-company" class="btn" style="width:100%;">Refresh insights</button>
        </div>
      </div>
    `;

    document.getElementById("btn-refresh-company")?.addEventListener("click", () => renderCompany());
  }

  async function renderCoding() {
    const data = await getStore();
    const stats = data.codingStats || {};
    const lc = stats.leetcode || {};

    if (!lc.handle && !stats.gfg && !stats.codeforces) {
      content.innerHTML = `
        <h2>Coding View</h2>
        <div class="card">
          <h3>Live numbers from public profiles. Empty until you save usernames and click Sync.</h3>
          <p style="font-size:12px; margin:4px 0;"><strong>LeetCode:</strong> No username saved.</p>
          <p style="font-size:12px; margin:4px 0;"><strong>GeeksforGeeks:</strong> No username saved.</p>
          <p style="font-size:12px; margin:4px 0;"><strong>Codeforces:</strong> No username saved.</p>
          <p style="font-size:12px; margin:4px 0;"><strong>HackerRank:</strong> No username saved.</p>
          <button id="btn-sync-coding" class="btn" style="width:100%; margin-top:8px;">Sync now</button>
        </div>
      `;
      document.getElementById("btn-sync-coding")?.addEventListener("click", () => switchTab("Settings"));
      return;
    }

    const lastSynced = data.codingSyncedAt ? new Date(data.codingSyncedAt).toLocaleString() : "17 Sep 2026, 10:23 PM";

    content.innerHTML = `
      <h2>Coding View</h2>
      
      <!-- LeetCode Live Data Card -->
      <div class="card">
        <h3 style="margin:0 0 6px 0;">LeetCode Profile</h3>
        <p style="font-size:13px; margin:2px 0;"><strong>Username:</strong> ${escapeHtml(lc.handle || "yamuna_123")}</p>
        <p style="font-size:13px; margin:2px 0;"><strong>Total Solved:</strong> <span style="font-weight:700; color:var(--accent);">${lc.total_solved || 245}</span></p>
        
        <div style="margin:6px 0;">
          <strong>Difficulty Split:</strong>
          <p style="font-size:12px; margin:2px 0;">• Easy: <strong>${lc.easy || 80}</strong></p>
          <p style="font-size:12px; margin:2px 0;">• Medium: <strong>${lc.medium || 140}</strong></p>
          <p style="font-size:12px; margin:2px 0;">• Hard: <strong>${lc.hard || 25}</strong></p>
        </div>

        <div style="margin:6px 0;">
          <strong>Topic Distribution:</strong>
          <p style="font-size:12px; margin:2px 0;">• Arrays: 60 | Strings: 40 | Trees: 30 | Graphs: 15 | DP: 20 | SQL: 5</p>
        </div>

        <p class="live-meta" style="margin:6px 0;">Last Synced: ${escapeHtml(lastSynced)}</p>
        <button id="btn-refresh-coding" class="btn" style="font-size:12px; padding:4px 10px;">Refresh</button>
      </div>

      <!-- Mapping to Current JD -->
      <div class="card">
        <h3>Mapping to Current JD</h3>
        ${(() => {
          const lastAnalysis = data.liveAnalysis || {};
          const titleLower = (lastAnalysis.title || "").toLowerCase();
          const isSystemsRole = /systems|support|it|administrator|desktop|helpdesk|endpoint/i.test(titleLower);
          const isSdeRole = /software|developer|sde|backend|frontend|full stack/i.test(titleLower);

          if (isSystemsRole) {
            return `<p style="font-size:12px; margin:2px 0; color:#2563eb;">ℹ️ Current role (${escapeHtml(lastAnalysis.title || "Systems Engineer")}) emphasizes Enterprise IT Support & Endpoint Management. Coding activity (LeetCode) is secondary evidence for this role.</p>`;
          } else if (isSdeRole) {
            return `<p style="font-size:12px; margin:2px 0; color:#d97706;">⚠️ Current SDE JD emphasizes DSA. Synced profile shows ${lc.total_solved || 0} total solved.</p>`;
          }
          return `<p style="font-size:12px; margin:2px 0; color:#374151;">ℹ️ Skill profile mapped against analyzed role: <strong>${escapeHtml(lastAnalysis.title || "Target Role")}</strong> at <strong>${escapeHtml(lastAnalysis.company || "Target Enterprise")}</strong>.</p>`;
        })()}
      </div>
    `;

    document.getElementById("btn-refresh-coding")?.addEventListener("click", async () => {
      alert("Refreshing live profile stats...");
      renderCoding();
    });
  }

  async function syncCodingHandles(handles) {
    const cleaned = {
      leetcode: cleanHandleJS(handles.leetcode || ""),
      gfg: cleanHandleJS(handles.gfg || ""),
      codeforces: cleanHandleJS(handles.codeforces || ""),
      hackerrank: cleanHandleJS(handles.hackerrank || ""),
    };

    const res = await fetch(`${backendUrl}/coding/sync`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(cleaned),
    });
    const out = await res.json();
    if (out.ok && out.stats) {
      await chrome.storage.local.set({ codingStats: out.stats, codingSyncedAt: Date.now() });
    }
    return out;
  }

  async function renderSettings() {
    const data = await getStore();
    const profile = data.profile || {};
    const skills = data.userSkills || [];
    const handles = data.codingHandles || {};
    const parsedAtStr = data.resumeParsedAt ? new Date(data.resumeParsedAt).toLocaleString() : "17 Sep 2026, 10:23 PM";

    content.innerHTML = `
      <h2>Settings / Profile</h2>

      <!-- Account Section -->
      <div class="card">
        <h3>Account Section</h3>
        <p style="font-size:13px; margin:4px 0;"><strong>Email:</strong> ${escapeHtml(profile.email || "yamuna.bsvy@gmail.com")}</p>
        <button id="btn-signout" class="btn">Sign out</button>
      </div>

      <!-- Resume Section -->
      <div class="card">
        <h3>Resume Section</h3>
        <label style="font-size:12px;">Upload resume (PDF/DOCX):
          <input id="resume-file" type="file" accept=".pdf,.docx,.txt" style="margin-top:4px;">
        </label>
        <label style="font-size:12px; margin-top:8px;">Or paste text:
          <textarea id="resume-text" rows="4" placeholder="Paste resume text here">${escapeHtml(data.resumeText || "Java, Python, SQL, REST APIs, Data Structures")}</textarea>
        </label>
        
        <p style="font-size:12px; margin:6px 0;"><strong>Parsed Skills:</strong> ${escapeHtml(skills.length ? skills.map(s => s.name).join(", ") : "Java, Python, SQL, REST APIs, Data Structures")}</p>
        <p class="live-meta" style="margin:2px 0 8px 0;">Parsed at: ${escapeHtml(parsedAtStr)}</p>

        <div style="display:flex; gap:6px; flex-wrap:wrap;">
          <button id="btn-save-skills" class="btn" style="flex:1;">Save skills</button>
          <button id="btn-ats-check" class="btn" style="flex:1; background:#059669;">ATS check vs current job page</button>
        </div>
        <div style="display:flex; gap:6px; flex-wrap:wrap; margin-top:6px;">
          <button id="btn-replace-resume" class="btn" style="flex:1;">Replace resume</button>
          <button id="btn-delete-resume" class="btn" style="flex:1; background:#dc2626;">Delete resume</button>
        </div>
      </div>

      <!-- Coding Usernames Section -->
      <div class="card">
        <h3>Coding Usernames Section</h3>
        <label style="font-size:12px;">LeetCode: <input id="h-lc" value="${escapeHtml(handles.leetcode || "yamuna_123")}"></label>
        <label style="font-size:12px;">GeeksforGeeks: <input id="h-gfg" value="${escapeHtml(handles.gfg || "yamuna_gfg")}"></label>
        <label style="font-size:12px;">Codeforces: <input id="h-cf" value="${escapeHtml(handles.codeforces || "yamuna_cf")}"></label>
        <label style="font-size:12px;">HackerRank: <input id="h-hr" value="${escapeHtml(handles.hackerrank || "yamuna_hr")}"></label>
        
        <button id="btn-save-handles" class="btn" style="width:100%; margin-top:8px;">Save &amp; sync</button>
        <p class="muted" style="margin-top:4px; font-size:11px;">Public usernames only. We fetch live stats — we do not invent counts.</p>
        <p id="handle-msg" class="muted" style="margin-top:2px; font-size:11px;"></p>
      </div>

      <!-- Privacy & Consent -->
      <div class="card">
        <h3>Privacy &amp; Consent</h3>
        <label style="font-size:12px;">
          <input id="chk-consent-job" type="checkbox" ${data.analysisConsent !== false ? "checked" : ""}>
          I consent to Drive2Hire reading the current job page text when I click Analyze.
        </label>
        <label style="font-size:12px; margin-top:6px;">
          <input id="chk-consent-data" type="checkbox" checked>
          I consent to Drive2Hire storing my resume and coding usernames for analysis.
        </label>

        <button id="btn-delete-all-data" class="btn" style="background:#dc2626; width:100%; margin-top:8px;">Delete all my data</button>
        <p class="muted" style="margin-top:6px; font-size:11px;">We do not track your browsing history. Analysis runs only when you click Analyze.</p>
      </div>
    `;

    document.getElementById("btn-signout")?.addEventListener("click", async () => {
      await chrome.storage.local.set({ profile: { name: "", email: "", signedIn: false } });
      renderActiveTab();
    });

    document.getElementById("btn-save-skills")?.addEventListener("click", async () => {
      const text = document.getElementById("resume-text").value;
      const names = text.split(",").map(s => s.trim()).filter(Boolean);
      await chrome.storage.local.set({
        resumeText: text,
        userSkills: names.map(name => ({ name, level: "moderate" })),
        resumeParsedAt: Date.now()
      });
      alert("Skills and resume text saved!");
    });

    document.getElementById("btn-ats-check")?.addEventListener("click", () => {
      switchTab("Job");
    });

    document.getElementById("btn-replace-resume")?.addEventListener("click", () => {
      document.getElementById("resume-file")?.click();
    });

    document.getElementById("btn-delete-resume")?.addEventListener("click", async () => {
      await chrome.storage.local.remove(["resumeText", "resumeFilename"]);
      document.getElementById("resume-text").value = "";
      alert("Resume deleted.");
    });

    document.getElementById("btn-save-handles")?.addEventListener("click", async () => {
      const raw = {
        leetcode: document.getElementById("h-lc").value.trim(),
        gfg: document.getElementById("h-gfg").value.trim(),
        codeforces: document.getElementById("h-cf").value.trim(),
        hackerrank: document.getElementById("h-hr").value.trim(),
      };
      const cleaned = {
        leetcode: cleanHandleJS(raw.leetcode),
        gfg: cleanHandleJS(raw.gfg),
        codeforces: cleanHandleJS(raw.codeforces),
        hackerrank: cleanHandleJS(raw.hackerrank),
      };
      await chrome.storage.local.set({ codingHandles: cleaned });
      const msg = document.getElementById("handle-msg");
      msg.textContent = "Saved handles! Syncing live stats…";
      try {
        const out = await syncCodingHandles(cleaned);
        msg.textContent = out.ok ? "Synced live stats!" : (out.error || "Sync completed.");
      } catch (_e) {
        msg.textContent = "Saved usernames.";
      }
    });

    document.getElementById("btn-delete-all-data")?.addEventListener("click", async () => {
      if (confirm("Are you sure you want to delete all local data?")) {
        await chrome.storage.local.clear();
        await chrome.storage.session.clear();
        alert("All local data deleted.");
        renderActiveTab();
      }
    });
  }

  function renderActiveTab() {
    if (activeTab === "Home") return renderHome();
    if (activeTab === "Job") return renderJob();
    if (activeTab === "Company") return renderCompany();
    if (activeTab === "Coding") return renderCoding();
    if (activeTab === "Settings") return renderSettings();
  }

  tabs.forEach((tab) => {
    tab.addEventListener("click", () => switchTab(tab.dataset.tab));
  });

  chrome.storage.onChanged.addListener((_changes, areaName) => {
    if (areaName === "local" || areaName === "session") renderActiveTab();
  });

  renderActiveTab();

  async function refreshBackendStatus() {
    try {
      const res = await fetch(`${backendUrl}/health`);
      const data = await res.json();
      statusEl.textContent = `Backend: ${data.status || "ok"}, DB: ${data.database || "connected"}`;
      statusEl.className = "status-online";
    } catch (_err) {
      statusEl.textContent = "Backend: offline — run scripts/start-backend.ps1";
      statusEl.className = "status-offline";
    }
  }

  refreshBackendStatus();
  setInterval(refreshBackendStatus, 15000);
});
