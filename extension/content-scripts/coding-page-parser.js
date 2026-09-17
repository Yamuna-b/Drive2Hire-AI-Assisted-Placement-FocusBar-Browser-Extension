// Real-time Coding Platform Content Script (LeetCode, GFG, Codeforces)
(function () {
  if (window.__drive2hireCodingParserLoaded) return;
  window.__drive2hireCodingParserLoaded = true;

  let sessionStartTime = Date.now();
  let solvedProblems = [];
  let currentProblem = null;

  function getPlatform() {
    const url = window.location.href;
    if (url.includes("leetcode.com")) return "leetcode";
    if (url.includes("geeksforgeeks.org")) return "gfg";
    if (url.includes("codeforces.com")) return "codeforces";
    if (url.includes("hackerrank.com")) return "hackerrank";
    return null;
  }

  function parseLeetCode() {
    const titleEl = document.querySelector('[data-cy="question-title"], .text-title-large, a.no-underline');
    const title = titleEl ? titleEl.innerText.replace(/^\d+\.\s*/, "").trim() : (document.title.split("-")[0] || "Two Sum").trim();

    // Difficulty selector
    let difficulty = "Medium";
    const diffEl = document.querySelector('[class*="text-difficulty-"], [class*="bg-fill-"]');
    if (diffEl) {
      const text = diffEl.innerText.toLowerCase();
      if (text.includes("easy")) difficulty = "Easy";
      else if (text.includes("hard")) difficulty = "Hard";
      else if (text.includes("medium")) difficulty = "Medium";
    }

    // Topic tags
    const topicEls = document.querySelectorAll('a[href*="/tag/"], .topic-tag, [class*="topic-tag"]');
    let topics = Array.from(topicEls).map(el => el.innerText.trim()).filter(Boolean);
    if (!topics.length) {
      if (title.toLowerCase().includes("two sum") || title.toLowerCase().includes("array")) topics = ["Arrays", "Hashing"];
      else if (title.toLowerCase().includes("tree") || title.toLowerCase().includes("binary")) topics = ["Trees"];
      else if (title.toLowerCase().includes("list")) topics = ["Linked Lists"];
      else topics = ["Arrays", "Hashing"];
    }

    return {
      platform: "leetcode",
      problem_id: title.toLowerCase().replace(/\s+/g, "-"),
      problem_name: title || "Two Sum",
      difficulty: difficulty,
      topic: topics[0] || "Arrays",
      topics: topics,
      url: window.location.href,
    };
  }

  function parseGFG() {
    const titleEl = document.querySelector(".problem-tab__name, h3, .g-m-0");
    const title = titleEl ? titleEl.innerText.trim() : document.title.split("|")[0].trim();
    return {
      platform: "gfg",
      problem_id: title.toLowerCase().replace(/\s+/g, "-"),
      problem_name: title || "Problem",
      difficulty: "Medium",
      topic: "DSA",
      topics: ["DSA"],
      url: window.location.href,
    };
  }

  function parseCodeforces() {
    const titleEl = document.querySelector(".title");
    const title = titleEl ? titleEl.innerText.trim() : document.title.split("-")[0].trim();
    return {
      platform: "codeforces",
      problem_id: title.toLowerCase().replace(/\s+/g, "-"),
      problem_name: title || "Problem",
      difficulty: "Medium",
      topic: "Implementation",
      topics: ["Implementation"],
      url: window.location.href,
    };
  }

  function extractCurrentProblem() {
    const platform = getPlatform();
    if (!platform) return null;
    if (platform === "leetcode") return parseLeetCode();
    if (platform === "gfg") return parseGFG();
    if (platform === "codeforces") return parseCodeforces();
    return null;
  }

  function updateLiveSession() {
    const prob = extractCurrentProblem();
    if (!prob) return;
    currentProblem = prob;

    const elapsedMs = Date.now() - sessionStartTime;
    const elapsedMins = Math.max(1, Math.floor(elapsedMs / 60000));

    // Check if user solved an accepted problem on screen
    const bodyText = document.body ? document.body.innerText : "";
    const isAccepted = /Accepted|Success|Wrong Answer|Time Limit Exceeded/i.test(bodyText);
    const isSuccess = /Accepted|100%|Score: 100/i.test(bodyText);

    chrome.runtime.sendMessage({
      type: "liveCodingUpdate",
      payload: {
        activeProblem: prob,
        elapsedMinutes: elapsedMins,
        isAccepted: isSuccess,
        timestamp: Date.now(),
      }
    });
  }

  // Periodic polling & DOM change monitoring
  setInterval(updateLiveSession, 3000);
  updateLiveSession();

  chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
    if (message?.type === "getCodingSessionState") {
      sendResponse({ ok: true, activeProblem: currentProblem, sessionStartTime });
      return true;
    }
  });
})();
