// Live page extractor — any website. Return value goes to the service worker.
(function () {
  function textOf(el) {
    return (el && el.innerText ? el.innerText : "").replace(/\s+/g, " ").trim();
  }

  function pickText(root, selectors) {
    for (let i = 0; i < selectors.length; i++) {
      const el = root.querySelector(selectors[i]);
      const t = textOf(el);
      if (t.length > 1 && t.length < 300) return t;
    }
    return "";
  }

  function pickLong(root, selectors) {
    for (let i = 0; i < selectors.length; i++) {
      const nodes = root.querySelectorAll(selectors[i]);
      let best = "";
      nodes.forEach((el) => {
        const t = el.innerText ? el.innerText.trim() : "";
        if (t.length > best.length) best = t;
      });
      if (best.length > 40) return best;
    }
    return "";
  }

  function meta(name) {
    const el =
      document.querySelector(`meta[property="${name}"]`) ||
      document.querySelector(`meta[name="${name}"]`);
    return el && el.content ? el.content.trim() : "";
  }

  function looksLikeJob(text, url) {
    const blob = `${url} ${text}`.toLowerCase();
    return /job|career|hiring|vacancy|apply|must have|responsibilit|qualification|linkedin\.com\/jobs|naukri|indeed/.test(
      blob
    );
  }

  const url = window.location.href;
  const root = document;

  let title = pickText(root, [
    "h1.job-details-jobs-unified-top-card__job-title",
    "h1.jobs-unified-top-card__job-title",
    "h1.t-24",
    "h1.topcard__title",
    "h1.jd-header-title",
    ".jobsearch-JobInfoHeader-title",
    "h1",
  ]);
  if (!title) title = (meta("og:title") || document.title || "").split("|")[0].trim();

  let company = pickText(root, [
    ".job-details-jobs-unified-top-card__company-name a",
    ".jobs-unified-top-card__company-name a",
    ".topcard__org-name-link",
    ".jd-header-comp-name",
    "a[href*='/company/']",
  ]);
  if (!company) {
    const og = meta("og:site_name");
    if (og && !/linkedin|naukri|indeed|google/i.test(og)) company = og;
  }

  let location = pickText(root, [
    ".job-details-jobs-unified-top-card__primary-description-container",
    ".jobs-unified-top-card__bullet",
    ".jobsearch-JobInfoHeader-subtitle",
  ]);

  let workMode = "";
  const pageText = document.body ? document.body.innerText : "";
  const modeMatch = pageText.match(/\b(On-site|Hybrid|Remote|Work from home)\b/i);
  if (modeMatch) workMode = modeMatch[1];

    let jd = pickLong(root, [
      ".jobs-description-content__text",
      ".jobs-description__content",
      ".jobs-box__html-content",
      "#job-details",
      ".jobsearch-JobComponent-description",
      ".dang-inner-html",
      "[class*='job-description']",
      "article",
    ]);
  if (!jd || jd.length < 80) {
    jd = (document.body && document.body.innerText) || "";
  }

  if (jd.length > 20000) jd = jd.slice(0, 20000);

  const isLinkedInJobView = /linkedin\.com\/jobs\/view\//.test(url);
  const hasJdMarkers = /must have skills|about the job|job description|key responsibilities|minimum qualifications/i.test(jd);
  const isJobListing = /\/jobs\/view\/|naukri\.com\/job|indeed\.com\/viewjob|glassdoor\..*job/i.test(url);

  if (!isLinkedInJobView && !isJobListing && !hasJdMarkers) {
    return {
      ok: false,
      reason: "not_a_job_posting",
      hint: "This is not a job posting. Open a single job (e.g. linkedin.com/jobs/view/...) then Analyze.",
    };
  }

  if (!title && !company && jd.length < 40) {
    return {
      ok: false,
      reason: "empty_page",
      hint: "This page has almost no readable text. Refresh and try again.",
    };
  }

  return {
    ok: true,
    payload: {
      title: title || "",
      company: company || "",
      location: location || "",
      work_mode: workMode,
      jd,
      source: url,
      is_job_like: looksLikeJob(jd, url),
    },
  };
})();
