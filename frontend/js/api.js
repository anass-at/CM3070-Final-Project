const API = 'http://localhost:8000/api/v1';

// save/get/remove tokens from localStorage
function saveToken(key, value) {
  localStorage.setItem(key, value);
}

function getToken(key) {
  return localStorage.getItem(key);
}

function clearToken(key) {
  localStorage.removeItem(key);
}

// redirect to login if no token found
function requireUserAuth() {
  if (!getToken('user_token')) {
    location.href = 'login.html';
  }
}

function requireCompanyAuth() {
  if (!getToken('company_token')) {
    location.href = 'login.html';
  }
}

function requireAdminAuth() {
  if (!getToken('admin_token')) {
    location.href = 'login.html';
  }
}

// send a POST request to the API
async function post(url, body, token = null) {
  const headers = { 'Content-Type': 'application/json' };
  if (token) {
    headers['Authorization'] = 'Bearer ' + token;
  }

  const response = await fetch(url, {
    method: 'POST',
    headers: headers,
    body: JSON.stringify(body)
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || 'Something went wrong');
  }
  return data;
}

// send a PUT request (used for profile updates)
async function put(url, body, token) {
  const response = await fetch(url, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer ' + token
    },
    body: JSON.stringify(body)
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || 'Something went wrong');
  }
  return data;
}

// send a GET request with the auth token
async function get(url, token) {
  const response = await fetch(url, {
    headers: { 'Authorization': 'Bearer ' + token }
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || 'Something went wrong');
  }
  return data;
}

// show a red error alert
function showError(id, msg) {
  const el = document.getElementById(id);
  el.className = 'alert alert-danger';
  el.textContent = msg;
  el.style.display = 'block';
}

// show a green success alert
function showSuccess(id, msg) {
  const el = document.getElementById(id);
  el.className = 'alert alert-success';
  el.textContent = msg;
  el.style.display = 'block';
}

function hideAlert(id) {
  document.getElementById(id).style.display = 'none';
}

// disable/enable button and swap the label while loading
function setLoading(btn, loading) {
  if (loading) {
    btn.disabled = true;
    btn.textContent = 'Please wait...';
  } else {
    btn.disabled = false;
    btn.textContent = btn.dataset.label;
  }
}

// logout functions - call the backend then clear the token
async function logoutUser() {
  try {
    await post(API + '/auth/logout', {}, getToken('user_token'));
  } catch (err) {
    console.log('Logout request failed, clearing token anyway');
  }
  clearToken('user_token');
  location.href = 'login.html';
}

async function logoutCompany() {
  try {
    await post(API + '/company/logout', {}, getToken('company_token'));
  } catch (err) {
    console.log('Logout request failed, clearing token anyway');
  }
  clearToken('company_token');
  location.href = 'login.html';
}

async function logoutAdmin() {
  try {
    await post(API + '/auth/logout', {}, getToken('admin_token'));
  } catch (err) {
    console.log('Logout request failed, clearing token anyway');
  }
  clearToken('admin_token');
  location.href = 'login.html';
}
