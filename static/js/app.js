(() => {
  const form        = document.getElementById('analyze-form');
  const submitBtn   = document.getElementById('submit-btn');
  const loading     = document.getElementById('loading');
  const errorBanner = document.getElementById('error-banner');
  const resultsSection = document.getElementById('results-section');
  const scoreDisplay   = document.getElementById('score-display');
  const scoreLabel     = document.getElementById('score-label');
  const hintsList      = document.getElementById('hints-list');
  const filterBtns     = document.querySelectorAll('.filter-btn');
  const pageScreenshot      = document.getElementById('page-screenshot');
  const previewUnavailable  = document.getElementById('preview-unavailable');
  const scoreThumbnailWrap  = document.getElementById('score-thumbnail-wrap');
  const scoreThumbnail      = document.getElementById('score-thumbnail');
  const similarityBar       = document.getElementById('similarity-bar');
  const similarityValue     = document.getElementById('similarity-value');
  const relevanceBar        = document.getElementById('relevance-bar');
  const relevanceValue      = document.getElementById('relevance-value');
  const tabBtns        = document.querySelectorAll('.tab-btn');

  let allHints = [];

  // ── Form submit ────────────────────────────────────────────────────────────
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    setLoading(true);
    clearError();
    resultsSection.hidden = true;

    const payload = {
      url: document.getElementById('url').value.trim(),
      search_query: document.getElementById('query').value.trim(),
    };

    try {
      const res = await fetch('/api/seo/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail ?? 'Unexpected error');
      }

      const data = await res.json();
      renderResults(data);
    } catch (err) {
      showError(err.message);
    } finally {
      setLoading(false);
    }
  });

  // ── Render ─────────────────────────────────────────────────────────────────
  function renderResults(data) {
    allHints = data.hints;

    // Score
    const score = data.score;
    scoreDisplay.textContent = score;
    scoreDisplay.className = 'score ' + scoreClass(score);
    scoreLabel.textContent = scoreDescription(score);

    // Screenshot
    if (data.page_image) {
      const src = `data:image/png;base64,${data.page_image}`;
      pageScreenshot.src = src;
      pageScreenshot.hidden = false;
      previewUnavailable.hidden = true;
      scoreThumbnail.src = src;
      scoreThumbnailWrap.hidden = false;
    } else {
      pageScreenshot.hidden = true;
      previewUnavailable.hidden = false;
      scoreThumbnailWrap.hidden = true;
    }

    // Semantic similarity
    if (data.semantic_similarity != null) {
      const pct = Math.round(data.semantic_similarity * 100);
      similarityBar.style.width = `${pct}%`;
      similarityBar.className = 'ai-metric-bar ' + aiScoreClass(pct);
      similarityValue.textContent = `${pct} / 100`;
    }

    // Relevance score
    if (data.relevance_score != null) {
      const pct = Math.round(data.relevance_score * 100);
      relevanceBar.style.width = `${pct}%`;
      relevanceBar.className = 'ai-metric-bar ' + aiScoreClass(pct);
      relevanceValue.textContent = `${pct} / 100`;
    }

    // Hints
    renderHints('all');
    activateFilter('all');

    resultsSection.hidden = false;
    resultsSection.scrollIntoView({ behavior: 'smooth' });
  }

  const _severityOrder = { critical: 0, warning: 1, info: 2 };
  const _severityLabel  = { critical: 'Critical', warning: 'Warning', info: 'Info' };

  function renderHints(severity) {
    hintsList.innerHTML = '';

    if (severity === 'all') {
      const groups = { critical: [], warning: [], info: [] };
      allHints.forEach(h => groups[h.severity]?.push(h));

      let anyRendered = false;
      ['critical', 'warning', 'info'].forEach(sev => {
        if (groups[sev].length === 0) return;
        anyRendered = true;

        const section = document.createElement('li');
        section.className = 'hint-group';
        section.innerHTML = `
          <div class="hint-group-header">
            <span class="hint-badge ${sev}">${_severityLabel[sev]}</span>
            <span class="hint-group-count">${groups[sev].length} hint${groups[sev].length !== 1 ? 's' : ''}</span>
          </div>
        `;

        const groupList = document.createElement('ul');
        groupList.className = 'hint-group-list';
        groups[sev].forEach(hint => groupList.appendChild(makeHintItem(hint)));
        section.appendChild(groupList);

        hintsList.appendChild(section);
      });

      if (!anyRendered) {
        hintsList.innerHTML = '<li style="color:#718096">No hints.</li>';
      }
    } else {
      const filtered = allHints.filter(h => h.severity === severity);
      if (filtered.length === 0) {
        hintsList.innerHTML = '<li style="color:#718096">No hints for this filter.</li>';
        return;
      }
      filtered.forEach(hint => hintsList.appendChild(makeHintItem(hint)));
    }
  }

  function makeHintItem(hint) {
    const li = document.createElement('li');
    li.className = `hint-item ${hint.severity}`;
    li.innerHTML = `
      <div class="hint-header">
        <span class="hint-badge ${hint.severity}">${hint.severity}</span>
        <span class="hint-category">${hint.category}</span>
      </div>
      <p class="hint-message">${escHtml(hint.message)}</p>
      <p class="hint-recommendation">${escHtml(hint.recommendation)}</p>
    `;
    return li;
  }

  // ── Tab buttons ────────────────────────────────────────────────────────────
  function activateTab(tabName) {
    tabBtns.forEach(b => b.classList.toggle('active', b.dataset.tab === tabName));
    document.querySelectorAll('.tab-panel').forEach(p => { p.hidden = true; });
    document.getElementById(`tab-${tabName}`).hidden = false;
  }

  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => activateTab(btn.dataset.tab));
  });

  document.getElementById('score-thumbnail-link').addEventListener('click', (e) => {
    e.preventDefault();
    activateTab('preview');
    document.getElementById('tab-preview').scrollIntoView({ behavior: 'smooth' });
  });

  // ── Filter buttons ─────────────────────────────────────────────────────────
  filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const severity = btn.dataset.severity;
      activateFilter(severity);
      renderHints(severity);
    });
  });

  function activateFilter(severity) {
    filterBtns.forEach(b => b.classList.toggle('active', b.dataset.severity === severity));
  }

  // ── Helpers ────────────────────────────────────────────────────────────────
  function setLoading(on) {
    loading.hidden = !on;
    submitBtn.disabled = on;
  }

  const HTTP_TIPS = {
    400: "The server couldn't understand the request — it may be malformed or missing required data.",
    401: "Authentication is required. You need to log in before accessing this resource.",
    403: "The server understood your request but refused to fulfill it — usually because you're not logged in, your session expired, or you don't have the right permissions.",
    404: "The page wasn't found. The URL may be wrong, or the page may have been moved or deleted.",
    405: "The request method isn't allowed for this URL (e.g. the server only accepts GET requests here).",
    408: "The server timed out waiting for the request. Try again — it may be a temporary network issue.",
    410: "This page is permanently gone and won't be coming back.",
    429: "Too many requests — the server is rate-limiting you. Wait a moment before trying again.",
    500: "Something went wrong on the server. This is the site's problem, not yours.",
    502: "The server received an invalid response from an upstream service. Usually temporary.",
    503: "The server is temporarily unavailable — it may be down for maintenance or overloaded.",
    504: "The server didn't get a response in time from an upstream service. Usually temporary.",
  };

  function showError(msg) {
    const match = msg.match(/\b([45]\d{2})\b/);
    const tip   = match ? HTTP_TIPS[parseInt(match[1], 10)] : null;

    errorBanner.innerHTML = '';

    const text = document.createElement('span');
    text.textContent = `Error: ${msg}`;
    errorBanner.appendChild(text);

    if (tip) {
      const wrap = document.createElement('span');
      wrap.className = 'error-tip-wrap';

      const icon = document.createElement('button');
      icon.className = 'error-tip-icon';
      icon.setAttribute('aria-label', 'What does this mean?');
      icon.textContent = 'i';

      const tooltip = document.createElement('span');
      tooltip.className = 'error-tip-tooltip';
      tooltip.textContent = tip;

      icon.addEventListener('click', (e) => {
        e.stopPropagation();
        tooltip.classList.toggle('visible');
      });
      document.addEventListener('click', () => tooltip.classList.remove('visible'), { once: false });

      wrap.appendChild(icon);
      wrap.appendChild(tooltip);
      errorBanner.appendChild(wrap);
    }

    errorBanner.hidden = false;
  }

  function clearError() {
    errorBanner.hidden = true;
    errorBanner.textContent = '';
  }

  function scoreClass(n) {
    if (n >= 80) return 'good';
    if (n >= 50) return 'average';
    return 'poor';
  }

  function aiScoreClass(n) {
    if (n > 70) return 'good';
    if (n > 50) return 'average';
    return 'poor';
  }

  function scoreDescription(n) {
    if (n >= 80) return 'Great — minor tweaks needed.';
    if (n >= 50) return 'Fair — several improvements recommended.';
    return 'Poor — significant SEO issues found.';
  }

  function escHtml(str) {
    return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  }
})();
