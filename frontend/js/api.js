const API = 'http://localhost:8000/api/v1';

// ── Token helpers ─────────────────────────────────────────────────
function saveToken(key, value) { localStorage.setItem(key, value); }
function getToken(key)         { return localStorage.getItem(key); }
function clearToken(key)       { localStorage.removeItem(key); }

// ── Redirect if not logged in ─────────────────────────────────────
function requireUserAuth()    { if (!getToken('user_token'))    location.href = 'login.html'; }
function requireCompanyAuth() { if (!getToken('company_token')) location.href = 'login.html'; }
function requireAdminAuth()   { if (!getToken('admin_token'))   location.href = 'login.html'; }

// ── Generic fetch wrappers ────────────────────────────────────────
async function post(url, body, token = null) {
  const headers = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(url, { method: 'POST', headers, body: JSON.stringify(body) });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Something went wrong');
  return data;
}

async function put(url, body, token) {
  const res = await fetch(url, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
    body: JSON.stringify(body)
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Something went wrong');
  return data;
}

async function get(url, token) {
  const res = await fetch(url, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Something went wrong');
  return data;
}

// ── UI helpers ────────────────────────────────────────────────────
function showError(id, msg)   { const el = document.getElementById(id); el.className = 'alert alert-danger'; el.textContent = msg; el.style.display = 'block'; }
function showSuccess(id, msg) { const el = document.getElementById(id); el.className = 'alert alert-success'; el.textContent = msg; el.style.display = 'block'; }
function hideAlert(id)        { document.getElementById(id).style.display = 'none'; }
function setLoading(btn, loading) {
  btn.disabled = loading;
  btn.textContent = loading ? 'Please wait...' : btn.dataset.label;
}

// ── Logout helpers ────────────────────────────────────────────────
async function logoutUser() {
  try { await post(`${API}/auth/logout`, {}, getToken('user_token')); } catch (_) {}
  clearToken('user_token');
  location.href = 'login.html';
}

async function logoutCompany() {
  try { await post(`${API}/company/logout`, {}, getToken('company_token')); } catch (_) {}
  clearToken('company_token');
  location.href = 'login.html';
}

async function logoutAdmin() {
  try { await post(`${API}/auth/logout`, {}, getToken('admin_token')); } catch (_) {}
  clearToken('admin_token');
  location.href = 'login.html';
}
