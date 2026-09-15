const BACKEND_URL = "http://127.0.0.1:8000";
const GOOGLE_CLIENT_ID =
  "758501915824-n03vtotgp025jc2gmn7hnsg5gh6lik0k.apps.googleusercontent.com";
const GOOGLE_SCOPES = [
  "openid",
  "email",
  "profile",
  "https://www.googleapis.com/auth/userinfo.email",
  "https://www.googleapis.com/auth/userinfo.profile",
].join(" ");

chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true }).catch(console.error);

chrome.tabs.onActivated.addListener(({ tabId }) => {
  chrome.storage.session.set({ linkedTabId: tabId });
});

chrome.runtime.onInstalled.addListener(async () => {
  await chrome.storage.local.remove(["lastJobAnalysis", "lastJobData"]);
  await chrome.storage.local.set({ googleClientId: GOOGLE_CLIENT_ID });
  const stored = await chrome.storage.local.get(["userSkills", "profile"]);
  if (!stored.userSkills) {
    await chrome.storage.local.set({ userSkills: [] });
  }
  if (!stored.profile) {
    await chrome.storage.local.set({
      profile: { name: "", email: "", signedIn: false },
    });
  }
});

async function analyseJob(payload, userSkills) {
  const stored = await chrome.storage.local.get(["resumeText", "codingStats"]);
  const response = await fetch(`${BACKEND_URL}/job/analyse`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      title: payload.title || "",
      company: payload.company || "",
      jd: payload.jd || "",
      location: payload.location || "",
      work_mode: payload.work_mode || "",
      page_url: payload.source || "",
      user_skills: userSkills || [],
      resume_text: stored.resumeText || "",
      coding_stats: stored.codingStats || {},
    }),
  });
  if (!response.ok) {
    throw new Error(`API ${response.status}: ${await response.text()}`);
  }
  return response.json();
}

async function handleJobData(payload) {
  const stored = await chrome.storage.local.get(["userSkills", "analysisConsent"]);
  if (!stored.analysisConsent) {
    throw new Error("Please review and accept the privacy controls in Settings before analyzing a page.");
  }
  const { userSkills = [] } = stored;
  const analysis = await analyseJob(payload, userSkills);
  await chrome.storage.session.set({
    liveJobData: payload,
    liveAnalysis: analysis,
    liveAnalysedAt: Date.now(),
  });
  await chrome.storage.local.remove(["lastJobAnalysis", "lastJobData"]);
  return analysis;
}

async function resolveTargetTab(preferredTabId) {
  if (preferredTabId) {
    try {
      return await chrome.tabs.get(preferredTabId);
    } catch (_e) {
      /* ignore */
    }
  }
  const bySession = await chrome.storage.session.get("linkedTabId");
  if (bySession.linkedTabId) {
    try {
      return await chrome.tabs.get(bySession.linkedTabId);
    } catch (_e) {
      /* ignore */
    }
  }
  const activeTabs = await chrome.tabs.query({ active: true, lastFocusedWindow: true });
  return activeTabs[0];
}

async function extractFromTab(tabId) {
  const injected = await chrome.scripting.executeScript({
    target: { tabId },
    files: ["content-scripts/page-extract.js"],
  });
  return injected && injected[0] ? injected[0].result : { ok: false, hint: "No extract result" };
}

async function analyseTabId(tabId) {
  const { analysisConsent } = await chrome.storage.local.get("analysisConsent");
  if (!analysisConsent) {
    return { ok: false, error: "Review and accept the privacy controls in Settings before analyzing a page." };
  }
  let tab;
  try {
    tab = await resolveTargetTab(tabId);
  } catch (_e) {
    return { ok: false, error: "No browser tab found." };
  }
  if (!tab?.id) return { ok: false, error: "No browser tab found." };
  if (/^chrome:|^chrome-extension:|^about:/i.test(tab.url || "")) {
    return { ok: false, error: "Open a normal website (not chrome:// pages), then Analyze." };
  }

  let result;
  try {
    result = await extractFromTab(tab.id);
  } catch (err) {
    return { ok: false, error: `Could not read this page. Refresh (F5) and retry. (${err.message})` };
  }
  if (!result?.ok) {
    return { ok: false, error: result?.hint || "Could not read text from this page." };
  }

  try {
    const analysis = await handleJobData(result.payload);
    return { ok: true, analysis };
  } catch (err) {
    return { ok: false, error: err.message || "Backend error. Is the server running?" };
  }
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (!message?.type) return false;
  if (message.type === "jobData") {
    handleJobData(message.payload)
      .then((analysis) => sendResponse({ ok: true, analysis }))
      .catch((err) => sendResponse({ ok: false, error: err.message }));
    return true;
  }
  if (message.type === "analyseCurrentTab") {
    analyseTabId(message.tabId)
      .then((response) => sendResponse(response))
      .catch((err) => sendResponse({ ok: false, error: err.message }));
    return true;
  }
  if (message.type === "ping") {
    sendResponse({ ok: true, backend: BACKEND_URL });
    return true;
  }
  if (message.type === "googleSignIn") {
    googleSignIn()
      .then((user) => sendResponse({ ok: true, user }))
      .catch((err) => sendResponse({ ok: false, error: err.message }));
    return true;
  }
  return false;
});

async function googleSignIn() {
  await chrome.storage.local.set({ googleClientId: GOOGLE_CLIENT_ID });
  const redirectUri = chrome.identity.getRedirectURL();
  let accessToken = null;
  let lastError = "";

  try {
    const tokenResult = await chrome.identity.getAuthToken({ interactive: true });
    accessToken = typeof tokenResult === "string" ? tokenResult : tokenResult?.token;
  } catch (err) {
    lastError = err.message || String(err);
  }

  if (!accessToken) {
    const authUrl =
      "https://accounts.google.com/o/oauth2/v2/auth" +
      `?client_id=${encodeURIComponent(GOOGLE_CLIENT_ID)}` +
      "&response_type=token" +
      `&redirect_uri=${encodeURIComponent(redirectUri)}` +
      `&scope=${encodeURIComponent(GOOGLE_SCOPES)}` +
      "&prompt=select_account" +
      "&include_granted_scopes=true";
    try {
      const responseUrl = await chrome.identity.launchWebAuthFlow({
        url: authUrl,
        interactive: true,
      });
      if (!responseUrl) throw new Error("Google sign-in was cancelled.");
      const fragment = responseUrl.split("#")[1] || responseUrl.split("?")[1] || "";
      const params = new URLSearchParams(fragment);
      accessToken = params.get("access_token");
      const oauthErr = params.get("error");
      if (oauthErr) {
        throw new Error(`Google error: ${oauthErr} (${params.get("error_description") || ""})`);
      }
    } catch (err) {
      lastError = err.message || String(err);
    }
  }

  if (!accessToken) {
    throw new Error(
      `Google sign-in failed. ${lastError} ` +
        `In Google Cloud → Credentials → your OAuth client, add this Authorized redirect URI: ${redirectUri} ` +
        `If the client type is "Web application", that URI is required. ` +
        `If the type is "Chrome extension", set Application ID to this extension's ID on chrome://extensions.`
    );
  }

  const user = await fetchGoogleUser(accessToken);
  await chrome.storage.local.set({
    profile: {
      name: user.name,
      email: user.email,
      picture: user.picture,
      signedIn: true,
      provider: "google",
    },
  });
  return user;
}

async function fetchGoogleUser(accessToken) {
  const googleRes = await fetch("https://www.googleapis.com/oauth2/v3/userinfo", {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  if (!googleRes.ok) {
    throw new Error("Google accepted login but userinfo failed. Try again.");
  }
  const info = await googleRes.json();
  const user = {
    name: info.name || "",
    email: info.email || "",
    picture: info.picture || "",
    google_id: info.sub || "",
  };

  try {
    await fetch(`${BACKEND_URL}/auth/google`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ access_token: accessToken }),
    });
  } catch (_e) {
    // Sign-in still succeeds locally if the backend is offline.
  }
  return user;
}
