const BACKEND_URL = 'http://127.0.0.1:8000';

const DEFAULT_USER_SKILLS = [
  { name: 'Python', level: 'strong', duration_bucket: '2+ years' },
  { name: 'JavaScript', level: 'moderate', duration_bucket: '1 year' },
  { name: 'SQL', level: 'moderate', duration_bucket: '1 year' },
  { name: 'Git', level: 'strong', duration_bucket: '2+ years' },
  { name: 'React', level: 'weak', duration_bucket: null },
  { name: 'DSA', level: 'moderate', duration_bucket: null },
  { name: 'REST', level: 'moderate', duration_bucket: null },
];

chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true }).catch(console.error);

// Remember which tab the user opened the panel from.
chrome.tabs.onActivated.addListener(({ tabId }) => {
  chrome.storage.session.set({ linkedTabId: tabId });
});

chrome.runtime.onInstalled.addListener(async () => {
  const stored = await chrome.storage.local.get('userSkills');
  if (!stored.userSkills) {
    await chrome.storage.local.set({ userSkills: DEFAULT_USER_SKILLS });
  }
});

async function analyseJob(payload, userSkills) {
  const response = await fetch(`${BACKEND_URL}/job/analyse`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      title: payload.title || '',
      company: payload.company || '',
      jd: payload.jd || '',
      user_skills: userSkills,
    }),
  });

  if (!response.ok) {
    const err = await response.text();
    throw new Error(`API ${response.status}: ${err}`);
  }

  return response.json();
}

async function handleJobData(payload) {
  const { userSkills = DEFAULT_USER_SKILLS } = await chrome.storage.local.get('userSkills');
  const analysis = await analyseJob(payload, userSkills);

  await chrome.storage.local.set({
    lastJobData: payload,
    lastJobAnalysis: analysis,
    lastAnalysedAt: Date.now(),
  });

  return analysis;
}

function isJobPageUrl(url) {
  if (!url) return false;
  return /linkedin\.com\/jobs/.test(url) || /naukri\.com\/(job-listings|job-detail)/.test(url);
}

async function resolveTargetTab(preferredTabId) {
  if (preferredTabId) {
    try {
      const tab = await chrome.tabs.get(preferredTabId);
      if (isJobPageUrl(tab.url)) return tab;
    } catch (_e) {
      // Tab closed — fall through.
    }
  }

  const bySession = await chrome.storage.session.get('linkedTabId');
  if (bySession.linkedTabId) {
    try {
      const tab = await chrome.tabs.get(bySession.linkedTabId);
      if (isJobPageUrl(tab.url)) return tab;
    } catch (_e) {
      // ignore
    }
  }

  const activeTabs = await chrome.tabs.query({ active: true, lastFocusedWindow: true });
  if (activeTabs[0] && isJobPageUrl(activeTabs[0].url)) {
    return activeTabs[0];
  }

  // Side panel focus can steal "active tab" — scan all tabs for a job page.
  const allTabs = await chrome.tabs.query({ currentWindow: true });
  const jobTab = allTabs.find((t) => isJobPageUrl(t.url));
  if (jobTab) return jobTab;

  return activeTabs[0] || allTabs[0];
}

async function extractFromTab(tabId) {
  // Ensure the parser script is injected (executeScript injects if not present)
  await chrome.scripting.executeScript({
    target: { tabId },
    files: ['content-scripts/job-page-parser.js'],
  });
  // Request the content script to extract job data via messaging
  return new Promise((resolve) => {
    chrome.tabs.sendMessage(tabId, { type: 'extractJob' }, (response) => {
      if (chrome.runtime.lastError) {
        console.error('Extraction message error:', chrome.runtime.lastError);
        resolve({ ok: false, error: chrome.runtime.lastError.message });
      } else {
        resolve(response);
      }
    });
  });
}

async function analyseTabId(tabId) {
  let tab;
  try {
    tab = tabId ? await chrome.tabs.get(tabId) : await resolveTargetTab();
  } catch (_e) {
    return { ok: false, error: 'No browser tab found. Click the LinkedIn tab, then try again.' };
  }

  if (!tab?.id) {
    return { ok: false, error: 'No browser tab found.' };
  }

  if (!isJobPageUrl(tab.url)) {
    return {
      ok: false,
      error: `Not a job page (got: ${tab.url || 'unknown'}). Open LinkedIn Jobs or Naukri job detail, then click Analyze.`,
    };
  }

  let result;
  try {
    result = await extractFromTab(tab.id);
    console.log('Extraction result from background:', result);
  } catch (err) {
    return {
      ok: false,
      error: `Could not read page — refresh the LinkedIn tab (F5), then retry. (${err.message})`,
    };
  }

  if (!result?.ok) {
    return { ok: false, error: result?.hint || 'Could not extract job data from this page.' };
  }

  try {
    const analysis = await handleJobData(result.payload);
    return { ok: true, analysis };
  } catch (err) {
    return { ok: false, error: err.message || 'Backend error.' };
  }
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (!message?.type) return false;

  if (message.type === 'jobData') {
    handleJobData(message.payload)
      .then((analysis) => sendResponse({ ok: true, analysis }))
      .catch((err) => sendResponse({ ok: false, error: err.message }));
    return true;
  }

  if (message.type === 'analyseCurrentTab') {
    analyseTabId(message.tabId)
      .then((response) => sendResponse(response))
      .catch((err) => sendResponse({ ok: false, error: err.message }));
    return true;
  }

  if (message.type === 'ping') {
    sendResponse({ ok: true, backend: BACKEND_URL });
    return true;
  }

  return false;
});
