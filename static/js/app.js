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
      pageScreenshot.src = `data:image/png;base64,${data.page_image}`;
      pageScreenshot.hidden = false;
      previewUnavailable.hidden = true;
    } else {
      pageScreenshot.hidden = true;
      previewUnavailable.hidden = false;
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
  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      tabBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      document.querySelectorAll('.tab-panel').forEach(p => { p.hidden = true; });
      document.getElementById(`tab-${btn.dataset.tab}`).hidden = false;
    });
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

  function showError(msg) {
    errorBanner.textContent = `Error: ${msg}`;
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

  function scoreDescription(n) {
    if (n >= 80) return 'Great — minor tweaks needed.';
    if (n >= 50) return 'Fair — several improvements recommended.';
    return 'Poor — significant SEO issues found.';
  }

  function escHtml(str) {
    return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  }
})();
