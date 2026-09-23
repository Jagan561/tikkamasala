/**
 * API client — wraps fetch with auth headers + error handling.
 */
const API_BASE = 'http://localhost:8000';

const api = {
  getToken() {
    return localStorage.getItem('tm_token');
  },
  setToken(t) {
    localStorage.setItem('tm_token', t);
  },
  clearToken() {
    localStorage.removeItem('tm_token');
    localStorage.removeItem('tm_user');
    localStorage.removeItem('tm_role');
  },

  headers(extra = {}) {
    const h = { 'Content-Type': 'application/json', ...extra };
    const token = this.getToken();
    if (token) h['Authorization'] = `Bearer ${token}`;
    return h;
  },

  async request(method, path, body = null, options = {}) {
    const url = `${API_BASE}${path}`;
    const config = {
      method,
      headers: this.headers(options.headers || {}),
    };
    if (body) config.body = JSON.stringify(body);

    let resp;
    try {
      resp = await fetch(url, config);
    } catch (err) {
      throw new Error('Network error — is the backend running?');
    }

    let data;
    try {
      data = await resp.json();
    } catch {
      data = {};
    }

    if (!resp.ok) {
      const msg = data?.detail || data?.message || `Error ${resp.status}`;
      throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg));
    }
    return data;
  },

  get(path)         { return this.request('GET',    path); },
  post(path, body)  { return this.request('POST',   path, body); },
  put(path, body)   { return this.request('PUT',    path, body); },
  patch(path, body) { return this.request('PATCH',  path, body); },
  del(path)         { return this.request('DELETE', path); },
};

/* ── Toast Notifications ── */
function showToast(message, type = 'info', duration = 4000) {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }
  const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <span class="toast-icon">${icons[type] || 'ℹ️'}</span>
    <span class="toast-msg">${message}</span>
    <button class="toast-close" onclick="this.parentElement.remove()">×</button>
  `;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.animation = 'slideOutRight .3s ease forwards';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

/* ── Loading state helpers ── */
function setLoading(btn, loading, text = 'Loading...') {
  if (!btn) return;
  if (loading) {
    btn.dataset.origText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = `<span class="spinner"></span> ${text}`;
  } else {
    btn.disabled = false;
    btn.innerHTML = btn.dataset.origText || text;
  }
}

/* ── Format helpers ── */
function formatPrice(n) { return '₹' + Number(n).toFixed(2).replace(/\.00$/, ''); }
function formatDate(d)  { return d ? new Date(d).toLocaleString('en-IN') : '—'; }
function timeAgo(d) {
  const diff = Date.now() - new Date(d).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1) return 'just now';
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}
