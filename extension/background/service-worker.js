// Service Worker for the extension – handles messages between content scripts, side panel, and backend
self.addEventListener('install', event => {
  console.log('Service worker installed');
});

self.addEventListener('activate', event => {
  console.log('Service worker activated');
});

self.addEventListener('message', async event => {
  const msg = event.data;
  if (msg && msg.type === 'jobData') {
    // Forward job data to backend for analysis
    try {
      const response = await fetch('http://localhost:8000/job/analyse', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(msg.payload)
      });
      const result = await response.json();
      // Send analysis result back to extension UI
      chrome.runtime.sendMessage({
        type: 'jobAnalysisResult',
        payload: result
      });
      console.log('Job analysis result sent', result);
    } catch (e) {
      console.error('Error calling backend', e);
    }
  } else {
    console.log('Received message', msg);
  }
});
