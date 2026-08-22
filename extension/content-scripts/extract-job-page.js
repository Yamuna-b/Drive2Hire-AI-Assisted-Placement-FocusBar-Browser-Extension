(function () {
  function pickText(root, selectors) {
    for (let i = 0; i < selectors.length; i++) {
      const el = root.querySelector(selectors[i]);
      const text = el && el.innerText ? el.innerText.trim() : '';
      if (text.length > 1) return text;
    }
    return '';
  }

  function pickAllText(root, selectors) {
    for (let i = 0; i < selectors.length; i++) {
      const nodes = root.querySelectorAll(selectors[i]);
      const parts = [];
      nodes.forEach((el) => {
        const text = el.innerText ? el.innerText.trim() : '';
        if (text.length > 20) parts.push(text);
      });
      if (parts.length) return parts.join('\n\n');
    }
    return '';
  }

  function pickRoot(selectors) {
    for (let i = 0; i < selectors.length; i++) {
      const el = document.querySelector(selectors[i]);
      if (el) return el;
    }
    return document;
  }

  const url = window.location.href;

  if (/linkedin\.com\/jobs/.test(url)) {
    const isJobView = /linkedin\.com\/jobs\/view\//.test(url);
    const root = isJobView
      ? document
      : pickRoot([
          '.jobs-search__job-details--container',
          '.jobs-details',
          '.job-view-layout',
          '.scaffold-layout__detail',
          'main',
        ]);

    let title = pickText(root, [
      'h1.job-details-jobs-unified-top-card__job-title',
      'h1.jobs-unified-top-card__job-title',
      'h1.t-24.t-bold.inline',
      'h1.t-24',
      'h1.topcard__title',
      '.job-details-jobs-unified-top-card__job-title',
      '[data-test-job-title]',
    ]);

    let company = pickText(root, [
      '.job-details-jobs-unified-top-card__company-name a',
      '.jobs-unified-top-card__company-name a',
      '.topcard__org-name-link',
      '.job-details-jobs-unified-top-card__company-name',
      '.jobs-unified-top-card__company-name',
    ]);

    let jd = pickAllText(root, [
      '.jobs-description-content__text',
      '.jobs-description__content',
      '.jobs-box__html-content',
      '.description__text',
      'article.jobs-description__container',
      '#job-details',
      '[data-test-description]',
    ]);

    if (!title) {
      const h1 = root.querySelector('h1');
      if (h1 && h1.innerText) title = h1.innerText.trim();
    }
    if (!title) {
      const ogTitle = document.querySelector('meta[property="og:title"]');
      if (ogTitle && ogTitle.content) {
        title = ogTitle.content.replace(/\s*\|\s*LinkedIn\s*$/i, '').trim();
      }
    }
    if (!company) {
      const topCard = root.querySelector('.job-details-jobs-unified-top-card, .jobs-unified-top-card, .topcard');
      const scope = topCard || root;
      const link = scope.querySelector('a[href*="/company/"]');
      if (link && link.innerText) company = link.innerText.trim();
    }
    if (!jd) {
      const desc = root.querySelector('[class*="description"]');
      if (desc && desc.innerText) jd = desc.innerText.trim();
    }
    if (!title && !company && !jd) {
      return { ok: false, reason: 'no_job_data', hint: isJobView ? 'Sign in to LinkedIn and refresh this page (F5), then try Analyze again.' : 'Click a job in the list, wait 2 seconds, then try Analyze again.' };
    }
    return { ok: true, payload: { title, company, jd, source: url } };
  }

  if (/naukri\.com\/(job-listings|job-detail)/.test(url)) {
    const root = document;
    const title = pickText(root, ['.jobTitle span', 'h1.jd-header-title']);
    const company = pickText(root, ['.compName', '.jd-header-comp-name']);
    const jd = pickText(root, ['.job-description', '.dang-inner-html', '.jd-desc']);
    if (!title && !company && !jd) {
      return { ok: false, reason: 'no_job_data', hint: 'Naukri job text not found. Refresh and try again.' };
    }
    return { ok: true, payload: { title, company, jd, source: url } };
  }

  return { ok: false, reason: 'not_job_url', hint: 'Open a LinkedIn Jobs page or Naukri job detail page first.' };
})();
