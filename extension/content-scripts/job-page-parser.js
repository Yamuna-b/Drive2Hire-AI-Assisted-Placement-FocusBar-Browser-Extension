// Content script to extract job details from LinkedIn and Naukri pages
// Sends the extracted data to the background service worker

function extractJobData() {
  let title = '';
  let company = '';
  let jd = '';

  const url = window.location.href;

  // LinkedIn job page detection
  if (url.includes('linkedin.com/jobs/view')) {
    title = document.querySelector('h1.topcard__title')?.innerText?.trim() || '';
    company = document.querySelector('.topcard__org-name-link')?.innerText?.trim() || '';
    jd = document.querySelector('.description__text')?.innerText?.trim() || '';
  }
  // Naukri job page detection (simplified selectors)
  else if (url.includes('naukri.com/job-detail')) {
    title = document.querySelector('.jobTitle span')?.innerText?.trim() || '';
    company = document.querySelector('.compName')?.innerText?.trim() || '';
    jd = document.querySelector('.job-description')?.innerText?.trim() || '';
  }

  if (title || company || jd) {
    chrome.runtime.sendMessage({
      type: 'jobData',
      payload: { title, company, jd }
    });
    console.log('Job data sent to background:', {title, company, jd});
  } else {
    console.log('Job parser: No recognizable job data on this page');
  }
}

// Run extraction after DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', extractJobData);
} else {
  extractJobData();
}
