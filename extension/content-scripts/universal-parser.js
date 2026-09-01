// Universal job page parser for ANY website
// Intelligently extracts job title, company, and description from generic job pages

if (window.__placementFocusBarUniversalParser) {
  // Already loaded
} else {
  window.__placementFocusBarUniversalParser = true;

  // Common job board detectors (priority order for targeted extraction)
  const KNOWN_SITES = {
    linkedin: (url) => /linkedin\.com\/jobs/.test(url),
    naukri: (url) => /naukri\.com\/(job-listings|job-detail)/.test(url),
    indeed: (url) => /indeed\.com/.test(url),
    glassdoor: (url) => /glassdoor\.(com|co|in)/.test(url),
    monster: (url) => /monster\.com/.test(url),
    dice: (url) => /dice\.com/.test(url),
    ziprecruiter: (url) => /ziprecruiter\.com/.test(url),
    hired: (url) => /hired\.com/.test(url),
    builtin: (url) => /builtin\.com/.test(url),
    toptal: (url) => /toptal\.com/.test(url),
    github: (url) => /github\.com\/.*\/jobs/.test(url),
    stackoverflow: (url) => /stackoverflow\.com\/jobs/.test(url),
    wellfound: (url) => /wellfound\.com/.test(url),
    angel: (url) => /angel\.co/.test(url),
  };

  // Detect if URL is a job posting page
  function isJobPage() {
    const url = window.location.href.toLowerCase();
    const keywords = ['job', 'career', 'hire', 'position', 'role', 'vacancy', 'opening', 'recruit', 'apply'];
    return keywords.some((kw) => url.includes(kw));
  }

  // Extract page content intelligently
  function extractPageContent() {
    // Get all visible text content
    const allText = document.body.innerText || '';
    
    // Get text from specific container-like elements
    const containers = document.querySelectorAll(
      'article, section, .job-description, .job-detail, .job-post, ' +
      '[data-testid*="description"], [data-testid*="job"], ' +
      '.position-detail, .job-body, .job-contents, main, .main-content'
    );
    
    let contentText = '';
    for (const el of containers) {
      const text = el.innerText || '';
      if (text.length > contentText.length) {
        contentText = text;
      }
    }
    
    return contentText || allText;
  }

  // Extract title from h1 or similar headings
  function extractTitle() {
    const candidates = [
      document.querySelector('h1'),
      document.querySelector('[data-testid*="title"]'),
      document.querySelector('.job-title'),
      document.querySelector('.position-title'),
      document.querySelector('h1.job-title'),
      document.querySelector('h1[data-test-job-title]'),
    ];
    
    for (const el of candidates) {
      const text = el?.innerText?.trim();
      if (text && text.length > 3 && text.length < 200) {
        return text;
      }
    }
    
    // Fallback: first h1 on page
    const h1 = document.querySelector('h1');
    return h1?.innerText?.trim() || '';
  }

  // Extract company name
  function extractCompany() {
    const candidates = [
      document.querySelector('[data-testid*="company"]'),
      document.querySelector('.company-name'),
      document.querySelector('.company'),
      document.querySelector('.employer-name'),
      document.querySelector('[data-testid*="employer"]'),
      document.querySelector('a[href*="/company/"]'),
    ];
    
    for (const el of candidates) {
      const text = el?.innerText?.trim();
      if (text && text.length > 1 && text.length < 100) {
        return text;
      }
    }
    
    // Fallback: look for company link in header
    const link = document.querySelector('a[href*="company"]');
    return link?.innerText?.trim() || '';
  }

  // Main extraction function
  function extractJobData() {
    const url = window.location.href;
    
    // Check if this looks like a job page
    if (!isJobPage()) {
      return null;
    }

    let title = extractTitle();
    let company = extractCompany();
    let jd = extractPageContent();

    // Filter: must have meaningful content
    if (!title || title.length < 3) {
      return null;
    }

    if (!jd || jd.length < 100) {
      return null;
    }

    // Clean up job description: remove excess whitespace
    jd = jd.replace(/\s+/g, ' ').trim();

    return { 
      title, 
      company: company || 'Unknown Company',
      jd,
      source: url,
      extracted_at: new Date().toISOString()
    };
  }

  // Send data to service worker
  function sendJobData() {
    const payload = extractJobData();
    if (!payload) {
      return {
        ok: false,
        reason: 'no_job_data',
        hint: 'Could not extract job data from this page. Make sure you\'re on a job posting page.',
      };
    }
    chrome.runtime.sendMessage({ type: 'jobData', payload });
    return { ok: true, payload };
  }

  window.__placementFocusBarUniversalExtract = sendJobData;

  // Auto-extraction with debouncing
  let lastPayloadKey = '';
  let debounceTimer = null;
  let extractionCount = 0;
  const MAX_EXTRACTIONS = 3; // Prevent excessive extraction

  function runExtraction() {
    if (extractionCount >= MAX_EXTRACTIONS) return;

    const payload = extractJobData();
    if (!payload) return;

    const key = `${payload.title}|${payload.company}|${payload.jd.length}`;
    if (key === lastPayloadKey) return;

    lastPayloadKey = key;
    extractionCount++;

    const result = sendJobData();
    if (result.ok) {
      console.log('[Drive2Hire] Job data extracted:', {
        title: result.payload.title,
        company: result.payload.company,
        jd_length: result.payload.jd.length
      });
    }
  }

  function scheduleExtraction() {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(runExtraction, 800);
  }

  // Observe DOM changes
  const observer = new MutationObserver(() => scheduleExtraction());

  function startObserver() {
    const target = document.querySelector('main') || document.querySelector('article') || document.body;
    if (target) {
      observer.observe(target, { childList: true, subtree: true, characterData: false });
    }
  }

  // Initialize on page load
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      runExtraction();
      startObserver();
    });
  } else {
    runExtraction();
    startObserver();
  }

  // Message listener for manual extraction
  chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
    if (message?.type === 'extractJob') {
      const fn = window.__placementFocusBarUniversalExtract || (() => ({ ok: false, reason: 'parser_not_loaded' }));
      sendResponse(fn());
      return true;
    }
    return false;
  });
}
