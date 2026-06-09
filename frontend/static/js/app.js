// Configuration — override via window.API_BASE_URL in deployment
const API_BASE = window.API_BASE_URL || '/api';
const POLL_INTERVAL_MS = 10_000;

// ── State ────────────────────────────────────────────────────
let token = localStorage.getItem('token') || null;
let currentDevice = null;
let pollTimer = null;
let eventsOffset = 0;
const EVENTS_PAGE = 20;

// ── DOM helpers ──────────────────────────────────────────────
const $ = id => document.getElementById(id);
const show = el => el.classList.remove('hidden');
const hide = el => el.classList.add('hidden');

// ── API ──────────────────────────────────────────────────────
async function apiFetch(path, opts = {}) {
  const headers = { 'Content-Type': 'application/json', ...(opts.headers || {}) };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(API_BASE + path, { ...opts, headers });
  if (res.status === 401) { logout(); return null; }
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

// ── Auth ─────────────────────────────────────────────────────
$('login-form').addEventListener('submit', async e => {
  e.preventDefault();
  const email = $('email').value;
  const password = $('password').value;
  const err = $('login-error');
  hide(err);
  try {
    const data = await fetch(API_BASE + '/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    if (!data.ok) { show(err); err.textContent = 'Invalid credentials'; return; }
    const json = await data.json();
    token = json.access_token;
    localStorage.setItem('token', token);
    await enterDashboard();
  } catch {
    show(err); err.textContent = 'Could not reach the server';
  }
});

$('logout-btn').addEventListener('click', logout);

function logout() {
  token = null;
  localStorage.removeItem('token');
  clearInterval(pollTimer);
  hide($('dashboard-screen'));
  show($('login-screen'));
}

// ── Dashboard init ───────────────────────────────────────────
async function enterDashboard() {
  try {
    const me = await apiFetch('/auth/me');
    if (!me) return;
    $('user-email').textContent = me.email;
  } catch { logout(); return; }

  hide($('login-screen'));
  show($('dashboard-screen'));
  await loadDevices();
}

async function loadDevices() {
  const devices = await apiFetch('/devices');
  if (!devices) return;
  const sel = $('device-select');
  sel.innerHTML = '';
  if (devices.length === 0) {
    sel.innerHTML = '<option value="">No devices found</option>';
    return;
  }
  devices.forEach(d => {
    const opt = document.createElement('option');
    opt.value = d.device_id;
    opt.textContent = `${d.name} (${d.device_id})`;
    sel.appendChild(opt);
  });
  currentDevice = devices[0].device_id;
  updateDashboard(devices[0]);
  await loadThresholds();
  await loadEvents(true);
  startPolling();
}

$('device-select').addEventListener('change', async e => {
  currentDevice = e.target.value;
  eventsOffset = 0;
  await poll();
  await loadThresholds();
  await loadEvents(true);
});

// ── Polling ──────────────────────────────────────────────────
function startPolling() {
  clearInterval(pollTimer);
  pollTimer = setInterval(poll, POLL_INTERVAL_MS);
}

async function poll() {
  if (!currentDevice) return;
  try {
    const data = await apiFetch(`/devices/${currentDevice}/latest`);
    if (data) updateDashboard(data);
  } catch { /* network blip, stay silent */ }
}

// ── Dashboard update ─────────────────────────────────────────
const THREAT_META = {
  'Safe':          { cls: 'threat-safe',          icon: '✓',  label: 'Safe' },
  'Intruder':      { cls: 'threat-intruder',       icon: '👤', label: 'Intruder' },
  'Fire':          { cls: 'threat-fire',           icon: '🔥', label: 'Fire' },
  'Possible Fire': { cls: 'threat-possible-fire',  icon: '🔶', label: 'Possible Fire' },
  'False Alarm':   { cls: 'threat-false-alarm',    icon: '🌡', label: 'False Alarm' },
  'Offline':       { cls: 'threat-safe',           icon: '?',  label: 'Offline' },
};

function updateDashboard(device) {
  const threat = device.threat || 'Safe';
  const meta = THREAT_META[threat] || THREAT_META['Safe'];
  const banner = $('threat-banner');

  // Update threat banner
  Object.values(THREAT_META).forEach(m => banner.classList.remove(m.cls));
  banner.classList.add(meta.cls);
  $('threat-icon').textContent = meta.icon;
  $('threat-label').textContent = meta.label;
  $('threat-score').textContent = `Risk: ${(device.risk_score || 0).toFixed(3)}`;

  // Connectivity
  const badge = $('connectivity-badge');
  const now = Date.now();
  const lastSeen = device.last_seen ? new Date(device.last_seen).getTime() : 0;
  const online = (now - lastSeen) < 60_000;
  badge.className = `badge ${online ? 'badge-online' : 'badge-offline'}`;
  badge.textContent = online ? 'Online' : 'Offline';

  // Last reading from state
  const r = device;
  $('r-temp').textContent = r.temperature_c != null ? `${r.temperature_c.toFixed(1)} °C` : '—';
  $('r-humidity').textContent = r.humidity_percent != null ? `${r.humidity_percent.toFixed(1)} %` : '—';
  $('r-light').textContent = r.light != null ? r.light : '—';
  $('r-flame').textContent = r.flame_detected != null ? (r.flame_detected ? '🔥 YES' : 'No') : '—';
  $('r-motion').textContent = r.motion_detected != null ? (r.motion_detected ? '🚨 YES' : 'No') : '—';
  $('r-armed').textContent = r.armed != null ? (r.armed ? '🔒 Armed' : '🔓 Disarmed') : '—';
  $('last-updated').textContent = device.last_seen ? new Date(device.last_seen).toLocaleString() : '—';
}

// Fetch latest reading detail (from last_reading in device_state)
async function refreshReadings() {
  if (!currentDevice) return;
  const data = await apiFetch(`/devices/${currentDevice}/readings?limit=1`);
  if (!data || data.length === 0) return;
  const r = data[0];
  $('r-temp').textContent = r.temperature_c != null ? `${r.temperature_c.toFixed(1)} °C` : '—';
  $('r-humidity').textContent = r.humidity_percent != null ? `${r.humidity_percent.toFixed(1)} %` : '—';
  $('r-light').textContent = r.light != null ? r.light : '—';
  $('r-flame').textContent = r.flame_detected != null ? (r.flame_detected ? '🔥 YES' : 'No') : '—';
  $('r-motion').textContent = r.motion_detected != null ? (r.motion_detected ? '🚨 YES' : 'No') : '—';
  $('r-armed').textContent = r.armed != null ? (r.armed ? '🔒 Armed' : '🔓 Disarmed') : '—';
  $('last-updated').textContent = r.timestamp ? new Date(r.timestamp).toLocaleString() : '—';
}

// ── Arm / Disarm ─────────────────────────────────────────────
$('arm-btn').addEventListener('click', async () => {
  if (!currentDevice) return;
  await apiFetch(`/devices/${currentDevice}/arm`, { method: 'POST' });
  await poll();
});

$('disarm-btn').addEventListener('click', async () => {
  if (!currentDevice) return;
  await apiFetch(`/devices/${currentDevice}/disarm`, { method: 'POST' });
  await poll();
});

// ── Thresholds ───────────────────────────────────────────────
async function loadThresholds() {
  if (!currentDevice) return;
  const data = await apiFetch(`/devices/${currentDevice}/thresholds`);
  if (!data) return;
  renderThresholdsView(data);
  fillThresholdsForm(data);
}

function renderThresholdsView(t) {
  const rows = [
    ['Light dark threshold', t.light_dark_threshold],
    ['Flame fire score', t.flame_fire_score],
    ['High temp (°C)', t.temp_high_c],
    ['Extreme temp (°C)', t.temp_extreme_c],
    ['Low humidity (%)', t.humidity_low_pct],
    ['Fire confirm score', t.fire_confirm_score],
    ['Fire alarm score', t.fire_alarm_score],
  ];
  $('thresholds-tbody').innerHTML = rows.map(([label, val]) =>
    `<tr><td>${label}</td><td>${val}</td></tr>`
  ).join('');
}

function fillThresholdsForm(t) {
  const form = $('thresholds-form');
  ['light_dark_threshold','flame_fire_score','temp_high_c','temp_extreme_c',
   'humidity_low_pct','fire_confirm_score','fire_alarm_score'].forEach(name => {
    const input = form.elements[name];
    if (input) input.value = t[name];
  });
}

$('thresholds-edit-btn').addEventListener('click', () => {
  hide($('thresholds-view'));
  show($('thresholds-form'));
});

$('thresholds-cancel-btn').addEventListener('click', () => {
  show($('thresholds-view'));
  hide($('thresholds-form'));
  hide($('thresholds-error'));
});

$('thresholds-form').addEventListener('submit', async e => {
  e.preventDefault();
  if (!currentDevice) return;
  const form = e.target;
  const body = {};
  new FormData(form).forEach((val, key) => { body[key] = parseFloat(val); });
  const err = $('thresholds-error');
  hide(err);
  try {
    const data = await apiFetch(`/devices/${currentDevice}/thresholds`, {
      method: 'PUT',
      body: JSON.stringify(body),
    });
    if (data) {
      renderThresholdsView(data);
      show($('thresholds-view'));
      hide(form);
    }
  } catch (ex) {
    show(err); err.textContent = 'Failed to save thresholds';
  }
});

// ── Events ───────────────────────────────────────────────────
async function loadEvents(reset = false) {
  if (!currentDevice) return;
  if (reset) { eventsOffset = 0; $('events-tbody').innerHTML = ''; }
  const data = await apiFetch(`/devices/${currentDevice}/events?limit=${EVENTS_PAGE}&offset=${eventsOffset}`);
  if (!data) return;

  const tbody = $('events-tbody');
  if (data.length === 0 && eventsOffset === 0) {
    tbody.innerHTML = '<tr><td colspan="4" class="empty-row">No events yet</td></tr>';
    return;
  }

  data.forEach(ev => {
    const cls = {
      'Fire':          'event-fire',
      'Intruder':      'event-intruder',
      'Possible Fire': 'event-possible-fire',
      'False Alarm':   'event-false-alarm',
      'Safe':          'event-safe',
    }[ev.event_type] || '';
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${new Date(ev.created_at).toLocaleString()}</td>
      <td class="${cls}">${ev.event_type}</td>
      <td>${ev.risk_score.toFixed(3)}</td>
      <td>${ev.alert_sent ? '✓' : '—'}</td>
    `;
    tbody.appendChild(tr);
  });
  eventsOffset += data.length;
}

$('load-more-events').addEventListener('click', () => loadEvents(false));

// ── Boot ─────────────────────────────────────────────────────
if (token) {
  enterDashboard();
}
