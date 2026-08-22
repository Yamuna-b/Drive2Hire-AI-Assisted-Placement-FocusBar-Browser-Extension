// Guard against double-injection when using scripting.executeScript fallback.
if (window.__placementFocusBarJobParser) {
  // Already loaded — still respond to extract messages.
} else {
  window.__placementFocusBarJobParser = true;

  const SITE_SELECTORS = {
    linkedin: {
      match: (url) => /linkedin\.com\/jobs/.test(url),
      detailRoot: [
        '.jobs-search__job-details--container',
        '.jobs-details',
        '.job-view-layout',
        '.scaffold-layout__detail',
        'main',
      ],
      title: [
        'h1.job-details-jobs-unified-top-card__job-title',
        'h1.jobs-unified-top-card__job-title',
        'h1.t-24.t-bold.inline',
        'h1.t-24',
        'h1.topcard__title',
        '.job-details-jobs-unified-top-card__job-title',
        '.jobs-unified-top-card__job-title h1',
        '[data-test-job-title]',
      ],
      company: [
        '.job-details-jobs-unified-top-card__company-name a',
        '.jobs-unified-top-card__company-name a',
        '.topcard__org-name-link',
        '.jobs-unified-top-card__subtitle-primary-grouping a',
        'a[href*="/company/"]',
      ],
      jd: [
        '.jobs-description-content__text',
        '.jobs-description__content',
        '.jobs-box__html-content',
        '.description__text',
        '#job-details',
        '[data-test-description]',
      ],
    },
    naukri: {
      match: (url) => /naukri\.com\/(job-listings|job-detail)/.test(url),
      detailRoot: ['body'],
      title: ['.jobTitle span', 'h1.jd-header-title', '.jd-header .title'],
      company: ['.compName', '.jd-header-comp-name', 'a.comp-name'],
      jd: ['.job-description', '.dang-inner-html', '.jd-desc'],
    },
  };

  function pickRoot(selectors) {
    for (const selector of selectors) {
      const el = document.querySelector(selector);
      if (el) return el;
    }
    return document;
  }

  function pickText(root, selectors) {
    for (const selector of selectors) {
      const el = root.querySelector(selector);
      const text = el?.innerText?.trim();
      if (text && text.length > 1) return text;
    }
    return '';
  }

  function linkedInFallback(root) {
    let title = '';
    let company = '';
    let jd = '';

    const h1 = root.querySelector('h1');
    if (h1?.innerText?.trim()) title = h1.innerText.trim();

    const companyLink = root.querySelector('a[href*="/company/"]');
    if (companyLink?.innerText?.trim()) company = companyLink.innerText.trim();

    const desc = root.querySelector('[class*="description"]');
    if (desc?.innerText?.trim()) jd = desc.innerText.trim();

    return { title, company, jd };
  }

  function getSiteConfig(url) {
    return Object.values(SITE_SELECTORS).find((site) => site.match(url));
  }

  function extractJobData() {
    const url = window.location.href;
    const site = getSiteConfig(url);
    if (!site) return null;

    const root = pickRoot(site.detailRoot || ['body']);
    let title = pickText(root, site.title);
    let company = pickText(root, site.company);
    let jd = pickText(root, site.jd);

    if (!title && !company && !jd && site === SITE_SELECTORS.linkedin) {
      const fb = linkedInFallback(root);
      title = fb.title;
      company = fb.company;
      jd = fb.jd;
    }

    if (!title && !company && !jd) return null;

    return { title, company, jd, source: url };
  }

  function sendJobData() {
    const payload = extractJobData();
    if (!payload) {
      return {
        ok: false,
        reason: 'no_job_data',
        hint: 'Could not read job fields. Try refreshing the page, or open the full job view URL (linkedin.com/jobs/view/...).',
      };
    }
    chrome.runtime.sendMessage({ type: 'jobData', payload });
    return { ok: true, payload };
  }

  window.__placementFocusBarExtract = sendJobData;

  let lastPayloadKey = '';
  let debounceTimer = null;

  function runExtraction() {
    const payload = extractJobData();
    if (!payload) return;

    const key = `${payload.title}|${payload.company}|${payload.jd.length}`;
    if (key === lastPayloadKey) return;
    lastPayloadKey = key;

    const result = sendJobData();
    if (result.ok) console.log('Job data extracted:', result.payload);
  }

  function scheduleExtraction() {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(runExtraction, 800);
  }

  const observer = new MutationObserver(() => scheduleExtraction());

  function startObserver() {
    const target = document.querySelector('main') || document.body;
    if (target) observer.observe(target, { childList: true, subtree: true });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      runExtraction();
      startObserver();
    });
  } else {
    runExtraction();
    startObserver();
  }
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message?.type === 'extractJob') {
    const fn = window.__placementFocusBarExtract || (() => ({ ok: false, reason: 'parser_not_loaded' }));
    sendResponse(fn());
    return true;
  }
  return false;
});
