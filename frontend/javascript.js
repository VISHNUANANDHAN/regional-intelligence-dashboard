
// Authentication guard
const API_BASE = 'https://regional-intelligence-backend.onrender.com';
(function () {
  const token = localStorage.getItem("access_token");

  if (!token) {
    window.location.replace("login.html");
    return;
  }

  // Verify that the saved token is still valid.
  fetch(`${API_BASE}/auth/me`, {
    headers: {
      Authorization: `Bearer ${token}`
    }
  })
    .then(response => {
      if (!response.ok) {
        localStorage.removeItem("access_token");
        localStorage.removeItem("user");
        window.location.replace("login.html");
      }
    })
    .catch(() => {
      console.error("Unable to verify the login session.");
    });
})();

'use strict';


// ── DOM ──────────────────────────────────────────────────────────
const locationInput  = document.getElementById('location-input');
const searchBtn      = document.getElementById('search-btn');
const inputError     = document.getElementById('input-error');

const loadingPanel   = document.getElementById('loading-panel');
const summarySection = document.getElementById('summary-section');
const eventsSection  = document.getElementById('events-section');
const emptySection   = document.getElementById('empty-section');
const errorSection   = document.getElementById('error-section');

const resultLocation = document.getElementById('result-location');
const weatherIcon    = document.getElementById('weather-icon');
const weatherTemp    = document.getElementById('weather-temp');
const weatherCondition = document.getElementById('weather-condition');
const weatherDesc    = document.getElementById('weather-desc');

const statusCard     = document.getElementById('status-card');
const statusIconWrap = document.getElementById('status-icon-wrap');
const statusIconEl   = document.getElementById('status-icon');
const statusHeadline = document.getElementById('status-headline');
const statusSub      = document.getElementById('status-sub');
const countBadge     = document.getElementById('count-badge');
const eventsList     = document.getElementById('events-list');
const eventsTally    = document.getElementById('events-tally');
const emptyLocation  = document.getElementById('empty-location');
const errorBody      = document.getElementById('error-body');
const retryBtn       = document.getElementById('retry-btn');
const loadingStepsEls = document.querySelectorAll('.lstep');
const saveReportBtn = document.getElementById("save-report-btn");
let currentReportData = null;

let lastQuery = '';
let stepTimer = null;

// ── VISIBILITY ───────────────────────────────────────────────────
function showOnly(...panels) {
  const all = [loadingPanel, summarySection, eventsSection, emptySection, errorSection];
  all.forEach(p => {
    if (panels.includes(p)) {
      p.hidden = false;
      p.classList.add('animate-in');
    } else {
      p.hidden = true;
      p.classList.remove('animate-in');
    }
  });
}

function hideAll() {
  showOnly(); // show none
}

// ── INPUT VALIDATION ─────────────────────────────────────────────
function setInputError(msg) {
  inputError.querySelector('span:last-child') && (inputError.querySelector('span:last-child').textContent = msg);
  inputError.hidden = false;
  locationInput.classList.add('input-invalid');
}

function clearInputError() {
  inputError.hidden = true;
  locationInput.classList.remove('input-invalid');
}

// ── LOADING STEPS ANIMATION ──────────────────────────────────────
function startLoadingSteps() {
  let step = 0;
  loadingStepsEls.forEach(s => s.classList.remove('is-active', 'is-done'));
  if (loadingStepsEls[0]) loadingStepsEls[0].classList.add('is-active');

  stepTimer = setInterval(() => {
    if (loadingStepsEls[step]) loadingStepsEls[step].classList.replace('is-active', 'is-done');
    step++;
    if (step < loadingStepsEls.length) {
      loadingStepsEls[step].classList.add('is-active');
    } else {
      clearInterval(stepTimer);
    }
  }, 900);
}

function stopLoadingSteps() {
  clearInterval(stepTimer);
  loadingStepsEls.forEach(s => {
    s.classList.remove('is-active');
    s.classList.add('is-done');
  });
}

// ── WEATHER ICONS ────────────────────────────────────────────────
function weatherIconClass(condition, desc) {
  const text = ((condition ?? '') + ' ' + (desc ?? '')).toLowerCase();
  if (text.includes('thunder') || text.includes('storm'))   return 'fa-cloud-bolt';
  if (text.includes('drizzle'))                              return 'fa-cloud-drizzle';
  if (text.includes('rain') || text.includes('shower'))     return 'fa-cloud-rain';
  if (text.includes('snow') || text.includes('sleet') || text.includes('blizzard')) return 'fa-snowflake';
  if (text.includes('fog') || text.includes('mist') || text.includes('haze')) return 'fa-smog';
  if (text.includes('clear') || text.includes('sunny'))     return 'fa-sun';
  if (text.includes('partly') || text.includes('few') || text.includes('scattered')) return 'fa-cloud-sun';
  if (text.includes('cloud') || text.includes('overcast') || text.includes('broken')) return 'fa-cloud';
  if (text.includes('wind'))                                 return 'fa-wind';
  return 'fa-cloud';
}

// ── RENDER WEATHER ───────────────────────────────────────────────
function renderWeather(data) {
  if (!data) return;
  const temp  = data.temperature ?? data.temp ?? null;
  const cond  = data.condition   ?? data.main ?? '—';
  const desc  = data.description ?? data.desc ?? '—';

  weatherTemp.textContent      = temp != null ? `${Math.round(temp)}°C` : '—';
  weatherCondition.textContent = cond;
  weatherDesc.textContent      = desc;

  const icon = weatherIconClass(cond, desc);
  weatherIcon.className = `fa-solid ${icon}`;
}

// ── RENDER STATUS ────────────────────────────────────────────────
function renderStatus(events) {
  const n = Array.isArray(events) ? events.length : 0;

  countBadge.textContent = n;
  eventsTally.textContent = `${n} event${n !== 1 ? 's' : ''}`;

  if (n === 0) {
    statusCard.className = 'card status-card status-clear';
    statusIconWrap.className = 'status-icon-wrap is-clear';
    statusIconEl.className = 'fa-solid fa-shield';
    statusHeadline.textContent = 'No Major Disruptions Detected';
    statusHeadline.className = 'status-headline is-clear';
    statusSub.textContent = 'Conditions appear normal for this location.';
    countBadge.className = 'count-badge';
  } else {
    statusCard.className = 'card status-card status-disruption';
    statusIconWrap.className = 'status-icon-wrap is-disruption';
    statusIconEl.className = 'fa-solid fa-triangle-exclamation';
    statusHeadline.textContent = 'Disruptions Detected';
    statusHeadline.className = 'status-headline is-disruption';
    statusSub.textContent = 'Active disruptions have been identified.';
    countBadge.className = 'count-badge is-disruption';
  }
}

// ── HTML ESCAPE ──────────────────────────────────────────────────
function esc(str) {
  const d = document.createElement('div');
  d.appendChild(document.createTextNode(String(str ?? '')));
  return d.innerHTML;
}

// ── RENDER EVENTS ─────────────────────────────────────────────── 
function renderEvents(events, location) {
  eventsList.innerHTML = '';
  emptyLocation.textContent = location || 'the selected location';

  if (!events || events.length === 0) {
    showOnly(summarySection, emptySection);
    return;
  }

  showOnly(summarySection, eventsSection);

  events.forEach((evt, i) => {
    const headline = evt.headline       ?? evt.title          ?? evt.news_headline  ?? 'No headline available';
    const category = evt.category       ?? evt.type           ?? 'General';
    const sector   = evt.sector         ?? evt.affected_sector ?? 'Unknown';
    const service  = evt.service        ?? evt.affected_service ?? evt.affected     ?? 'N/A';
    const source   = evt.source         ?? evt.news_source    ?? 'Unknown source';
    const url      = evt.url            ?? evt.link           ?? evt.article_url    ?? null;

    const card = document.createElement('div');
    card.className = 'event-card';

    const articleBtn = url
      ? `<a href="${esc(url)}" target="_blank" rel="noopener noreferrer" class="btn-article">
           <i class="fa-solid fa-arrow-up-right-from-square"></i> View Article
         </a>`
      : `<button class="btn-article" disabled style="opacity:0.45;cursor:default;">
           <i class="fa-solid fa-ban"></i> No Link
         </button>`;

    card.innerHTML = `
      <div class="event-card-main">
        <p class="event-headline">${esc(headline)}</p>
        <div class="event-badges">
          <span class="badge badge-category"><i class="fa-solid fa-tag"></i>${esc(category)}</span>
          <span class="badge badge-sector"><i class="fa-solid fa-building"></i>${esc(sector)}</span>
          <span class="badge badge-service"><i class="fa-solid fa-gears"></i>${esc(service)}</span>
        </div>
        <p class="event-source">
          <i class="fa-regular fa-newspaper"></i>
          Source: <strong>${esc(source)}</strong>
        </p>
      </div>
      <div class="event-action">${articleBtn}</div>
    `;

    eventsList.appendChild(card);

    // Stagger reveal
    requestAnimationFrame(() => {
      setTimeout(() => card.classList.add('visible'), i * 70);
    });
  });
}

// ── SHOW ERROR ───────────────────────────────────────────────────
function showError(msg) {
  errorBody.textContent = msg || 'An unexpected error occurred. Please try again.';
  showOnly(errorSection);
}



// ── DEMO TOAST ───────────────────────────────────────────────────
function showDemoToast() {
  const existing = document.getElementById('demo-toast');
  if (existing) existing.remove();

  const toast = document.createElement('div');
  toast.id = 'demo-toast';
  toast.setAttribute('role', 'alert');
  toast.style.cssText = `
    position: fixed; bottom: 28px; left: 50%; transform: translateX(-50%);
    background: #1B3A6B; color: #fff;
    padding: 11px 22px; border-radius: 8px;
    font-family: 'Inter', sans-serif; font-size: 13px; font-weight: 500;
    box-shadow: 0 4px 16px rgba(0,0,0,0.18);
    display: flex; align-items: center; gap: 10px;
    z-index: 9999; white-space: nowrap;
    animation: fade-slide-up 0.3s ease;
  `;
  toast.innerHTML = `<i class="fa-solid fa-flask" style="font-size:14px;opacity:0.8;"></i>
    Demo mode — backend unavailable. Displaying sample data.`;
  document.body.appendChild(toast);
  setTimeout(() => {
    toast.style.transition = 'opacity 0.4s ease';
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 400);
  }, 5000);
}

// ── MAIN ANALYZE ─────────────────────────────────────────────────

function present(data, location, isDemo) {

    if (data.error) {
        showError(data.error);
        return;
    }

    const events = data.detected_events || [];

    renderWeather(data.weather);

    renderStatus(events);

    renderEvents(events, location);

    if (isDemo) {
        showDemoToast();
    }
}

function delay(ms) {
  return new Promise(r => setTimeout(r, ms));
}

// ── EVENT LISTENERS ───────────────────────────────────────────────
searchBtn.addEventListener('click', analyze);

locationInput.addEventListener('keydown', e => {
  if (e.key === 'Enter') analyze();
});

locationInput.addEventListener('input', () => {
  if (locationInput.value.trim()) clearInputError();
});

retryBtn.addEventListener('click', () => {
  if (lastQuery) {
    locationInput.value = lastQuery;
    analyze();
  }
});

// Focus input on load
locationInput.focus();async function analyze() {
  const query = locationInput.value.trim();

  if (!query) {
    setInputError('Please enter a location to start the analysis.');
    locationInput.focus();
    return;
  }

  clearInputError();
  lastQuery = query;
  resultLocation.textContent = query;

  hideAll();
  showOnly(loadingPanel);
  startLoadingSteps();

  let data = null;

  try {
    const controller = new AbortController();

    const timeout = setTimeout(
        () => controller.abort(),
        90000
    );

    const res = await fetch(
        `${API_BASE}/report?location=${encodeURIComponent(query)}`,
        {
            signal: controller.signal
        }
    );

    clearTimeout(timeout);
    if (!res.ok) {
      let errMsg = `The server returned an error (${res.status}).`;
      try {
        const j = await res.json();
        if (j.error || j.message) errMsg = j.error ?? j.message;
      } catch (_) {}
      throw new Error(errMsg);
    }

    data = await res.json();

    if (data.error) {
        throw new Error(data.error);
    }

  } catch (err) {

    stopLoadingSteps();
    await delay(350);

    if (err.name === 'AbortError') {
        showError(
            'The analysis is taking longer than expected. Please try again.'
        );

    } else if (
        err.message.toLowerCase().includes('fetch') ||
        err.message.toLowerCase().includes('failed') ||
        err.message.toLowerCase().includes('network') ||
        err.message.toLowerCase().includes('load failed')
    ) {

        showError(
            'Unable to connect to the server.'
        );

    } else {

        showError(err.message);

    }

    return;
}
  stopLoadingSteps();
  await delay(350);
  present(data, query, false);
}
