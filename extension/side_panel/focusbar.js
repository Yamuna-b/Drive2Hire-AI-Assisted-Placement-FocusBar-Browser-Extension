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

  function emptyBlock(title, text) {
    return `<div class="card"><h3>${title}</h3><p class="muted">${text}</p></div>`;
  }

  function liveMeta(source, timestamp, confidence) {
    return `<p class="live-meta">Source: ${escapeHtml(source || "current page")} · Updated: ${timestamp ? new Date(timestamp).toLocaleString() : "just now"} · Confidence: ${escapeHtml(confidence || "needs review")}</p>`;
  }

  function readinessRows(items) {
    if (!items?.length) return `<p class="muted">None found from the available evidence.</p>`;
    return items.map((item) => `<div class="finding finding-${escapeHtml(item.status)}">
      <div><strong>${escapeHtml(item.skill)}</strong><span class="finding-status">${escapeHtml(item.status)}</span></div>
      <p>${escapeHtml(item.evidence?.join(" + ") || "No evidence found")}</p>
      <p class="muted">${escapeHtml(item.priority)} priority · ${escapeHtml(item.action)}</p>
    </div>`).join("");
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
    ]);
    const session = await chrome.storage.session.get(["liveAnalysis", "liveJobData"]);
    return { ...local, liveAnalysis: session.liveAnalysis, liveJobData: session.liveJobData };
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
        <label>Name<br><input id="auth-name" type="text" placeholder="Your name"></label>
        <label>Email<br><input id="auth-email" type="email" placeholder="you@example.com"></label>
        <button id="btn-signin" class="btn">Continue without Google</button>
      </div>
    `;
    document.getElementById("btn-google").addEventListener("click", () => {
      const errEl = document.getElementById("google-error");
      errEl.textContent = "Opening Google…";
      chrome.runtime.sendMessage({ type: "googleSignIn" }, (res) => {
        if (chrome.runtime.lastError) {
          errEl.textContent = chrome.runtime.lastError.message;
          return;
        }
        if (!res?.ok) {
          errEl.textContent = res?.error || "Google sign-in failed";
          return;
        }
        renderActiveTab();
      });
    });
    document.getElementById("btn-signin").addEventListener("click", async () => {
      const name = document.getElementById("auth-name").value.trim();
      const email = document.getElementById("auth-email").value.trim();
      if (!name || !email) return;
      await chrome.storage.local.set({ profile: { name, email, signedIn: true } });
      renderActiveTab();
    });
  }

  async function renderHome() {
    const data = await getStore();
    const profile = data.profile || {};
    if (!profile.signedIn) {
      renderSignIn();
      return;
    }
    const sessions = data.codingSessions || [];
    const apps = data.applications || [];
    const saved = data.savedJobs || [];
    const last = data.liveAnalysis;

    const stats = data.codingStats || {};
    const lc = stats.leetcode || {};
    content.innerHTML = `
      <h2>Home</h2>
      <p class="welcome-line">Welcome ${escapeHtml(profile.name || "there")}</p>
      <button id="btn-home-analyse" class="btn">Analyze current job</button>
      <div class="card">
        <h3>Coding (live sync)</h3>
        ${
          lc.ok
            ? `<p>LeetCode @${escapeHtml(lc.handle)}: ${lc.total_solved} solved (Easy ${lc.easy} / Med ${lc.medium} / Hard ${lc.hard})</p>`
            : `<p class="muted">No live stats yet. Add your public usernames in Settings → Sync now.</p>`
        }
      </div>
      <div class="card">
        <h3>Last analyzed page</h3>
        ${
          last
            ? `<p><strong>${escapeHtml(last.title || "Untitled")}</strong><br>${escapeHtml(last.company || "")}</p>
              <p>Readiness: ${last.readiness?.score ?? last.match_percent ?? 0}%</p>
              ${liveMeta(last.extraction?.source || last.page_url, last.retrieved_at, last.extraction?.confidence)}`
            : `<p class="muted">Open any job page and use the Job tab → Analyze this page.</p>`
        }
      </div>
      <div class="card">
        <h3>Applications</h3>
        ${
          apps.length
            ? apps.map((a) => `<p>${escapeHtml(a.title)} — ${escapeHtml(a.company)} (${escapeHtml(a.status)})</p>`).join("")
            : `<p class="muted">None logged yet.</p><button id="btn-home-applications" class="btn">Analyze current job</button>`
        }
      </div>
      <div class="card">
        <h3>Saved jobs</h3>
        ${
          saved.length
            ? saved.map((j) => `<p>${escapeHtml(j.title)} — ${escapeHtml(j.company)}</p>`).join("")
            : `<p class="muted">Empty until you save a job from the Job tab.</p><button id="btn-home-saved" class="btn">View current job</button>`
        }
      </div>
      <div class="card">
        <h3>Quick stats</h3>
        <p>Skills in profile: ${(data.userSkills || []).length}</p>
        <p>Jobs applied (logged): ${apps.filter((a) => a.status === "applied").length}</p>
      </div>
    `;
    document.getElementById("btn-home-analyse")?.addEventListener("click", () => {
      activeTab = "Job";
      tabs.forEach((tab) => tab.classList.toggle("active", tab.dataset.tab === "Job"));
      renderActiveTab();
    });
    document.getElementById("btn-home-applications")?.addEventListener("click", () => {
      activeTab = "Job";
      tabs.forEach((tab) => tab.classList.toggle("active", tab.dataset.tab === "Job"));
      renderActiveTab();
    });
    document.getElementById("btn-home-saved")?.addEventListener("click", () => {
      activeTab = "Job";
      tabs.forEach((tab) => tab.classList.toggle("active", tab.dataset.tab === "Job"));
      renderActiveTab();
    });
  }

  function bindAnalyse(onDone) {
    const btn = document.getElementById("btn-analyse");
    if (!btn) return;
    btn.addEventListener("click", () => {
      btn.disabled = true;
      const stages = ["Reading job page…", "Extracting requirements…", "Matching profile and resume…", "Checking coding evidence…"];
      let stage = 0;
      btn.textContent = stages[stage];
      const stageTimer = setInterval(() => {
        stage = Math.min(stage + 1, stages.length - 1);
        btn.textContent = stages[stage];
      }, 900);
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
      content.innerHTML = `<p class="error">${escapeHtml(error)}</p><button id="btn-analyse" class="btn">Analyze this page</button>`;
      bindAnalyse((a, e) => renderJob(a, e));
      return;
    }

    if (!analysis) {
      content.innerHTML = `
        <h2>Job</h2>
        ${emptyBlock("Live page analysis", "Open a supported job posting and click Analyze. We read the visible page text only after you ask us to.")}
        <button id="btn-analyse" class="btn">Analyze this page</button>
      `;
      bindAnalyse((a, e) => renderJob(a, e));
      return;
    }

    const match = analysis.match || { covered: [], weak: [], missing: [] };
    const exp = analysis.experience || {};
    const readiness = analysis.readiness || { score: analysis.match_percent || 0, findings: [] };
    content.innerHTML = `
      <h2>Job analysis</h2>
      <div class="job-snapshot">
        <h2>${escapeHtml(analysis.title || "Could not read title")}</h2>
        <p class="company">${escapeHtml(analysis.company || "Could not read company")}</p>
        <p class="muted">${escapeHtml(analysis.location || "")} ${escapeHtml(analysis.work_mode || "")}</p>
        <p><strong>Readiness: ${readiness.score}%</strong></p>
        <p class="muted">${escapeHtml(readiness.formula || "Based on live evidence available now.")}</p>
        ${liveMeta(analysis.extraction?.source || analysis.page_url, analysis.retrieved_at, analysis.extraction?.confidence)}
        <p class="muted">Review detected details before relying on this result.</p>
      </div>
      <div class="card readiness-report">
        <h3>Readiness report</h3>
        <div class="skill-group"><strong>Matched evidence</strong>${readinessRows(readiness.matched)}</div>
        <div class="skill-group"><strong>Missing required skills</strong>${readinessRows(readiness.missing_required)}</div>
        <div class="skill-group"><strong>Weak or insufficient evidence</strong>${readinessRows(readiness.weak_evidence)}</div>
      </div>
      <div class="skill-group"><strong>Mandatory (from this JD)</strong>${tags(analysis.mandatory_skills, "mandatory")}</div>
      <div class="skill-group"><strong>Nice-to-have (from this JD)</strong>${tags(analysis.nice_to_have_skills, "nice")}</div>
      ${
        exp.minimum_years
          ? `<p>Experience stated on page: ${exp.minimum_years}+ years${exp.focus_skill ? " (" + escapeHtml(exp.focus_skill) + ")" : ""}</p>`
          : ""
      }
      ${exp.education ? `<p>Education stated on page: ${escapeHtml(exp.education)}</p>` : ""}
      ${exp.employment_type ? `<p>Employment type stated on page: ${escapeHtml(exp.employment_type)}</p>` : ""}
      <div class="match-section">
        <strong>Your match</strong>
        <div class="skill-group"><strong>Covered</strong>${tags(match.covered, "covered")}</div>
        <div class="skill-group"><strong>Weak</strong>${tags(match.weak, "weak")}</div>
        <div class="skill-group"><strong>Missing</strong>${tags(match.missing, "missing")}</div>
      </div>
      <p class="muted">Source URL: ${escapeHtml(analysis.page_url || "Unavailable")}</p>
      <button id="btn-analyse" class="btn">Analyze this page</button>
      <button id="btn-save-job" class="btn">Save job</button>
      <button id="btn-qa" class="btn">Refine skills Q&amp;A</button>
      <div class="card">
        <h3>Log outcome</h3>
        <select id="outcome-status">
          <option value="applied">Applied</option>
          <option value="shortlisted">Shortlisted</option>
          <option value="interview">Interview</option>
          <option value="offered">Offered</option>
          <option value="rejected">Rejected</option>
        </select>
        <button id="btn-log" class="btn">Save status</button>
      </div>
    `;
    bindAnalyse((a, e) => renderJob(a, e));

    document.getElementById("btn-save-job")?.addEventListener("click", async () => {
      const saved = data.savedJobs || [];
      saved.unshift({ title: analysis.title, company: analysis.company, url: analysis.page_url, analysis: structuredClone(analysis), at: Date.now() });
      await chrome.storage.local.set({ savedJobs: saved.slice(0, 50) });
    });

    document.getElementById("btn-log")?.addEventListener("click", async () => {
      const apps = data.applications || [];
      apps.unshift({
        title: analysis.title,
        company: analysis.company,
        status: document.getElementById("outcome-status").value,
        analysis: structuredClone(analysis),
        at: Date.now(),
      });
      await chrome.storage.local.set({ applications: apps });
    });

    document.getElementById("btn-qa")?.addEventListener("click", () => {
      const missing = match.missing || [];
      if (!missing.length) {
        alert("No missing skills on this JD vs your profile.");
        return;
      }
      const overlay = document.createElement("div");
      overlay.id = "qa-modal-overlay";
      overlay.innerHTML = `<div id="qa-modal"><h2>Skill Q&amp;A</h2>
        ${missing
          .map(
            (name, i) => `
          <p><strong>${escapeHtml(name)}</strong></p>
          <label>Have you used this?
            <select id="qa-has-${i}"><option value="no">No</option><option value="yes">Yes</option></select>
          </label>
          <label>Duration <input id="qa-dur-${i}" placeholder="e.g. 1-2 years"></label>
          <label>Notes <textarea id="qa-notes-${i}"></textarea></label>
        `
          )
          .join("")}
        <button id="qa-save" class="btn">Save to profile</button>
        <button id="qa-close" class="btn">Close</button>
      </div>`;
      document.body.appendChild(overlay);
      document.getElementById("qa-close").onclick = () => overlay.remove();
      document.getElementById("qa-save").onclick = async () => {
        const skills = data.userSkills || [];
        missing.forEach((name, i) => {
          if (document.getElementById(`qa-has-${i}`).value !== "yes") return;
          const entry = {
            name,
            level: "moderate",
            duration_bucket: document.getElementById(`qa-dur-${i}`).value || null,
            project_notes: document.getElementById(`qa-notes-${i}`).value || null,
          };
          const idx = skills.findIndex((s) => s.name.toLowerCase() === name.toLowerCase());
          if (idx >= 0) skills[idx] = { ...skills[idx], ...entry };
          else skills.push(entry);
        });
        await chrome.storage.local.set({ userSkills: skills });
        overlay.remove();
        chrome.runtime.sendMessage({ type: "analyseCurrentTab" }, (res) => {
          if (res?.ok) renderJob(res.analysis, null);
        });
      };
    });
  }

  async function renderCompany() {
    const data = await getStore();
    const last = data.liveAnalysis;
    const payload = data.liveJobData || {};
    if (!last) {
      content.innerHTML = `${emptyBlock("Company", "Analyze a job page first. Insights come from that page, not a generic company template.")}
        <button id="btn-analyse" class="btn">Analyze this page</button>`;
      bindAnalyse(() => renderCompany());
      return;
    }
    content.innerHTML = `<p class="muted">Reading company facts from the last analyzed page…</p>`;
    try {
      const res = await fetch(`${backendUrl}/company/from-page`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          company_name: last.company,
          job_title: last.title,
          jd: payload.jd || "",
          location: last.location || payload.location || "",
          page_url: last.page_url || payload.source || "",
        }),
      });
      const info = await res.json();
      content.innerHTML = `
        <h2>Company</h2>
        <div class="card">
          <h3>${escapeHtml(info.name)}</h3>
          <p>${escapeHtml(info.job_title || "")}</p>
          <p class="muted">${escapeHtml(info.note || "")}</p>
        </div>
        <div class="card">
          <h3>From this posting</h3>
          <p>Location: ${escapeHtml((info.locations || []).join(", ") || "Not stated on page")}</p>
          <p>Skills on this JD:</p>
          ${tags(info.tech_stack, "mandatory")}
        </div>
        <div class="card">
          <h3>Salary / leadership</h3>
          <p class="muted">Not filled from static data. Add a salary API or confirm a source later.</p>
        </div>
        <button id="btn-analyse" class="btn">Re-read current page</button>
      `;
      bindAnalyse(() => renderCompany());
    } catch (err) {
      content.innerHTML = `<p class="error">${escapeHtml(err.message)}</p>`;
    }
  }

  function renderPlatformCard(label, stat, syncedAt) {
    if (!stat) return `<div class="card"><h3>${label}</h3><p class="muted">No username saved.</p></div>`;
    if (!stat.ok) return `<div class="card"><h3>${label}</h3><p class="error">${escapeHtml(stat.error || "Sync failed")}</p></div>`;
    const lines = Object.entries(stat)
      .filter(([k]) => !["ok", "platform", "source", "error"].includes(k))
      .map(([k, v]) => `<p>${escapeHtml(k)}: ${escapeHtml(v)}</p>`)
      .join("");
    return `<div class="card"><h3>${label}</h3>${lines}<p class="muted">Source: ${escapeHtml(stat.source || "unknown")} · Updated: ${syncedAt ? new Date(syncedAt).toLocaleString() : "unknown"}</p></div>`;
  }

  async function syncCodingHandles(handles) {
    const res = await fetch(`${backendUrl}/coding/sync`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        leetcode: handles.leetcode || "",
        gfg: handles.gfg || "",
        codeforces: handles.codeforces || "",
        hackerrank: handles.hackerrank || "",
      }),
    });
    const out = await res.json();
    if (out.ok && out.stats) {
      await chrome.storage.local.set({ codingStats: out.stats, codingSyncedAt: Date.now() });
    }
    return out;
  }

  async function renderCoding() {
    const data = await getStore();
    const handles = data.codingHandles || {};
    const stats = data.codingStats || {};
    content.innerHTML = `
      <h2>Coding</h2>
      <p class="muted">Live numbers from public profiles. Empty until you save usernames and click Sync.</p>
      <button id="btn-coding-settings" class="btn">Go to settings</button>
      ${renderPlatformCard("LeetCode", stats.leetcode, data.codingSyncedAt)}
      ${renderPlatformCard("GeeksforGeeks", stats.gfg, data.codingSyncedAt)}
      ${renderPlatformCard("Codeforces", stats.codeforces, data.codingSyncedAt)}
      ${renderPlatformCard("HackerRank", stats.hackerrank, data.codingSyncedAt)}
      <button id="btn-sync-coding" class="btn">Sync now</button>
      <p id="sync-msg" class="muted"></p>
    `;
    document.getElementById("btn-coding-settings").onclick = () => {
      activeTab = "Settings";
      tabs.forEach((tab) => tab.classList.toggle("active", tab.dataset.tab === "Settings"));
      renderActiveTab();
    };
    document.getElementById("btn-sync-coding").onclick = async () => {
      const msg = document.getElementById("sync-msg");
      msg.textContent = "Fetching live stats…";
      try {
        const out = await syncCodingHandles(handles);
        if (!out.ok) {
          msg.textContent = out.error || "Sync failed. Save usernames in Settings first.";
          return;
        }
        renderCoding();
      } catch (err) {
        msg.textContent = "Analysis service unavailable. Please try again later.";
      }
    };
  }

  async function renderSettings() {
    const data = await getStore();
    const profile = data.profile || {};
    const skills = data.userSkills || [];
    const handles = data.codingHandles || {};
    content.innerHTML = `
      <h2>Settings / Profile</h2>
      <div class="card">
        <h3>Account</h3>
        <p>${escapeHtml(profile.name || "")} ${escapeHtml(profile.email || "")}</p>
        <button id="btn-signout" class="btn">Sign out</button>
      </div>
      <div class="card">
        <h3>Privacy and data</h3>
        <p class="muted">Drive2Hire reads visible text only after you click Analyze. Resume text stays in this browser unless you connect a future account service. Only public coding usernames are synced.</p>
        <label><input id="analysis-consent" type="checkbox" ${data.analysisConsent ? "checked" : ""}> I understand and consent to live analysis when I click Analyze.</label>
        <button id="btn-delete-resume" class="btn">Delete saved resume</button>
        <button id="btn-delete-data" class="btn">Delete local profile data</button>
        <p id="privacy-msg" class="muted"></p>
      </div>
      <div class="card">
        <h3>Resume</h3>
        <input id="resume-file" type="file" accept=".pdf,.docx,.txt">
        <button id="btn-upload-resume" class="btn">Upload resume</button>
        <textarea id="resume-text" rows="6" placeholder="Or paste resume text">${escapeHtml(data.resumeText || "")}</textarea>
        <button id="btn-save-resume" class="btn">Save pasted text</button>
        <button id="btn-ats" class="btn">Resume-JD Match Score</button>
        <pre id="ats-out" class="muted"></pre>
      </div>
      <div class="card">
        <h3>Technical skills</h3>
        <textarea id="skills-text" rows="4" placeholder="Comma-separated, e.g. Python, SQL, Java">${escapeHtml(skills.map((s) => s.name).join(", "))}</textarea>
        <button id="btn-save-skills" class="btn">Save skills</button>
      </div>
      <div class="card">
        <h3>Coding usernames</h3>
        <label>LeetCode <input id="h-lc" value="${escapeHtml(handles.leetcode || "")}"></label>
        <label>GeeksforGeeks <input id="h-gfg" value="${escapeHtml(handles.gfg || "")}"></label>
        <label>Codeforces <input id="h-cf" value="${escapeHtml(handles.codeforces || "")}"></label>
        <label>HackerRank <input id="h-hr" value="${escapeHtml(handles.hackerrank || "")}"></label>
        <button id="btn-save-handles" class="btn">Save &amp; sync</button>
        <p id="handle-msg" class="muted">Public usernames only. We fetch live stats — we do not invent counts.</p>
      </div>
    `;
    document.getElementById("btn-signout").onclick = async () => {
      await chrome.storage.local.set({ profile: { name: "", email: "", signedIn: false } });
      renderActiveTab();
    };
    document.getElementById("analysis-consent").onchange = async (event) => {
      await chrome.storage.local.set({ analysisConsent: event.target.checked });
    };
    document.getElementById("btn-delete-resume").onclick = async () => {
      await chrome.storage.local.remove(["resumeText", "resumeFilename"]);
      document.getElementById("resume-text").value = "";
      document.getElementById("privacy-msg").textContent = "Saved resume deleted from this browser.";
    };
    document.getElementById("btn-delete-data").onclick = async () => {
      await chrome.storage.local.clear();
      await chrome.storage.session.clear();
      document.getElementById("privacy-msg").textContent = "Local profile data deleted. Reload the panel to sign in again.";
    };
    document.getElementById("btn-upload-resume").onclick = async () => {
      const file = document.getElementById("resume-file").files[0];
      if (!file) {
        alert("Choose a PDF, DOCX, or TXT file first.");
        return;
      }
      const form = new FormData();
      form.append("file", file);
      const output = document.getElementById("ats-out");
      output.textContent = "Reading resume…";
      try {
        const res = await fetch(`${backendUrl}/user/resume/upload`, { method: "POST", body: form });
        const out = await res.json();
        if (!res.ok) throw new Error(out.detail || `Upload failed (${res.status})`);
        document.getElementById("resume-text").value = out.resume_text;
        await chrome.storage.local.set({ resumeText: out.resume_text, resumeFilename: out.filename });
        output.textContent = `Uploaded ${out.filename} (${out.chars} characters).`;
      } catch (err) {
        output.textContent = `Resume upload failed: ${err.message}. Please try again later.`;
      }
    };
    document.getElementById("btn-save-resume").onclick = async () => {
      await chrome.storage.local.set({ resumeText: document.getElementById("resume-text").value });
    };
    document.getElementById("btn-save-skills").onclick = async () => {
      const names = document
        .getElementById("skills-text")
        .value.split(",")
        .map((s) => s.trim())
        .filter(Boolean);
      await chrome.storage.local.set({
        userSkills: names.map((name) => ({ name, level: "moderate", duration_bucket: null })),
      });
    };
    document.getElementById("btn-save-handles").onclick = async () => {
      const codingHandles = {
        leetcode: document.getElementById("h-lc").value.trim(),
        gfg: document.getElementById("h-gfg").value.trim(),
        codeforces: document.getElementById("h-cf").value.trim(),
        hackerrank: document.getElementById("h-hr").value.trim(),
      };
      await chrome.storage.local.set({ codingHandles });
      const msg = document.getElementById("handle-msg");
      msg.textContent = "Saved. Fetching live stats…";
      try {
        const out = await syncCodingHandles(codingHandles);
        msg.textContent = out.ok ? "Synced. Open the Coding tab to see numbers." : (out.error || "Sync failed");
      } catch (err) {
        msg.textContent = "Saved usernames, but live sync is unavailable right now.";
      }
    };
    document.getElementById("btn-ats").onclick = async () => {
      const last = data.liveAnalysis;
      const resume = document.getElementById("resume-text").value;
      if (!resume) {
        document.getElementById("ats-out").textContent = "Upload or paste resume text first.";
        return;
      }
      const output = document.getElementById("ats-out");
      output.textContent = "Checking resume…";
      try {
        const res = await fetch(`${backendUrl}/user/resume/check`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            resume_text: resume,
            jd_text: (data.liveJobData && data.liveJobData.jd) || "",
            mandatory_skills: last?.mandatory_skills || [],
            nice_to_have_skills: last?.nice_to_have_skills || [],
          }),
        });
        const out = await res.json();
        if (!res.ok) throw new Error(out.detail || `ATS check failed (${res.status})`);
        output.textContent = JSON.stringify(out, null, 2);
      } catch (err) {
        output.textContent = `ATS check failed: ${err.message}. Analyze a job and confirm the backend is running.`;
      }
    };
  }

  function renderActiveTab() {
    chrome.storage.local.get("profile", (data) => {
      const p = data.profile || {};
    });
    if (activeTab === "Home") return renderHome();
    if (activeTab === "Job") return renderJob();
    if (activeTab === "Company") return renderCompany();
    if (activeTab === "Coding") return renderCoding();
    if (activeTab === "Settings") return renderSettings();
  }

  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      tabs.forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      activeTab = tab.dataset.tab;
      renderActiveTab();
    });
  });

  chrome.storage.onChanged.addListener((_changes, areaName) => {
    if (areaName === "local" || areaName === "session") renderActiveTab();
  });

  chrome.storage.local.remove(["lastJobAnalysis", "lastJobData"]);
  renderActiveTab();

  async function refreshBackendStatus() {
    try {
      const res = await fetch(`${backendUrl}/health`);
      const data = await res.json();
      statusEl.textContent = `Backend: ${data.status}, DB: ${data.database}`;
      statusEl.className = data.status === "ok" ? "status-online" : "status-offline";
    } catch (_err) {
      statusEl.textContent = "Analysis service unavailable. Please try again later.";
      statusEl.className = "status-offline";
    }
  }

  refreshBackendStatus();
  setInterval(refreshBackendStatus, 15000);
});
