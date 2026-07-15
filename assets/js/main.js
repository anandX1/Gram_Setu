/* ═══════════════════════════════════════════
   AI GramSetu – Shared JS (assets/js/main.js)
   ═══════════════════════════════════════════ */

/* ── DATABASE ── */
const DB_KEY = 'gramsetu_db';

function getDB() {
  try { return JSON.parse(localStorage.getItem(DB_KEY)) || defaultDB(); }
  catch { return defaultDB(); }
}
function defaultDB() {
  return { workers: [], jobs: [], sms: [], feedback: [], training: [], attendance: {}, payments: [], sms_count: 0 };
}
function saveDB(db) { localStorage.setItem(DB_KEY, JSON.stringify(db)); }

/* ── TOAST ── */
function showToast(msg, type = 'success') {
  let t = document.getElementById('toast');
  if (!t) { t = document.createElement('div'); t.id = 'toast'; t.className = 'toast'; document.body.appendChild(t); }
  t.className = 'toast' + (type === 'error' ? ' error' : '');
  t.textContent = msg;
  
  // Force a browser reflow to restart CSS transitions
  void t.offsetWidth;
  
  t.classList.add('show');
  
  if (t._timer) clearTimeout(t._timer);
  t._timer = setTimeout(() => {
    t.classList.remove('show');
  }, 3000);
}

/* ── HELPERS ── */
function getInitials(name) {
  return (name || '?').split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2);
}
function fmtDate(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
}
function fmtCurrency(n) { return '₹' + Number(n || 0).toLocaleString('en-IN'); }

/* ── SIDEBAR HTML ── */
const NAV_ITEMS = [
  { label: 'DASHBOARD', section: true },
  { id: 'dashboard', label: 'Dashboard', href: '../pages/dashboard.html', icon: '<rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>' },
  { id: 'workers',   label: 'Workers',   href: '../pages/workers.html',   icon: '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>' },
  { id: 'jobs',      label: 'Jobs',      href: '../pages/jobs.html',      icon: '<rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2"/>' },
  { id: 'sms',       label: 'SMS Center',href: '../pages/sms.html',       icon: '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>' },
  { id: 'reports',   label: 'Reports',   href: '../pages/reports.html',   icon: '<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>' },
  { label: 'MANAGEMENT', section: true },
  { id: 'feedback',  label: 'Feedback',  href: '../pages/feedback.html',  icon: '<circle cx="12" cy="12" r="10"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/>' },
  { id: 'training',  label: 'Training',  href: '../pages/training.html',  icon: '<path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/>' },
  { id: 'attendance',label: 'Attendance',href: '../pages/attendance.html',icon: '<rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>' },
  { id: 'payments',  label: 'Payments',  href: '../pages/payments.html',  icon: '<line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>' },
  { id: 'ml-insights',label:'ML Insights',href:'../pages/ml-insights.html',icon:'<circle cx="12" cy="12" r="10"/><path d="M12 8v4l3 3"/>' },
];

function buildSidebar(activeId) {
  const nav = document.getElementById('sidebarNav');
  if (!nav) return;
  nav.innerHTML = NAV_ITEMS.map(item => {
    if (item.section) return `<div class="nav-section-label">${item.label}</div>`;
    const active = item.id === activeId ? 'active' : '';
    return `<a class="nav-item ${active}" href="${item.href}">
      <svg viewBox="0 0 24 24">${item.icon}</svg>
      ${item.label}
      ${active ? '<span class="nav-arrow">›</span>' : ''}
    </a>`;
  }).join('');
}

/* ── MOBILE RESPONSIVENESS ── */
function toggleMobileMenu() {
  const sidebar = document.querySelector('.sidebar');
  if (!sidebar) return;
  
  let overlay = document.querySelector('.sidebar-overlay');
  if (!overlay) {
    overlay = document.createElement('div');
    overlay.className = 'sidebar-overlay';
    document.body.appendChild(overlay);
    overlay.addEventListener('click', toggleMobileMenu);
  }
  
  sidebar.classList.toggle('open');
  overlay.classList.toggle('open');
}
