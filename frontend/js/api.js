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

// redirect to login if no token or token is expired
function requireUserAuth() {
  if (isTokenExpired(getToken('user_token'))) {
    handleUnauthorized();
  }
}

function requireCompanyAuth() {
  if (isTokenExpired(getToken('company_token'))) {
    handleUnauthorized();
  }
}

function requireAdminAuth() {
  if (isTokenExpired(getToken('admin_token'))) {
    handleUnauthorized();
  }
}

// decode JWT expiry without a library (payload is plain base64)
function isTokenExpired(token) {
  if (!token) return true;
  try {
    var payload = JSON.parse(atob(token.split('.')[1]));
    return payload.exp * 1000 < Date.now();
  } catch (e) {
    return true;
  }
}

// clear all tokens and go to login (relative path works from any portal folder)
function handleUnauthorized() {
  clearToken('user_token');
  clearToken('company_token');
  clearToken('admin_token');
  window.location.replace('login.html');
}

// turn a Pydantic error type into a short human message
function friendlyValidationMsg(err) {
  var type = err.type || '';
  var field = (err.loc || []).filter(function (l) { return l !== 'body'; }).join(', ');
  var label = field ? field.replace(/_/g, ' ') + ': ' : '';

  if (type === 'missing')           return label + 'This field is required';
  if (type === 'string_too_short')  return label + 'Too short';
  if (type === 'string_too_long')   return label + 'Too long';
  if (type === 'value_error') {
    if (err.loc && err.loc.indexOf('email') !== -1) return label + 'Enter a valid email address';
    return label + 'Invalid value';
  }
  if (type === 'int_parsing')       return label + 'Must be a number';
  if (type === 'date_from_datetime_inexact' || type === 'date_parsing') return label + 'Enter a valid date';

  // fallback: strip the verbose Pydantic prefix ("value is not a valid X: <reason>")
  var msg = err.msg || 'Invalid value';
  var colonIdx = msg.indexOf(': ');
  if (colonIdx !== -1) msg = msg.slice(colonIdx + 2);
  return label + msg;
}

// extract a readable message from a FastAPI error response
// detail can be a string (HTTPException) or an array of objects (validation error)
function extractError(data) {
  if (!data || !data.detail) return 'Something went wrong';
  if (Array.isArray(data.detail)) {
    return friendlyValidationMsg(data.detail[0]);
  }
  return data.detail;
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

  if (response.status === 401) {
    handleUnauthorized();
    return;
  }

  const data = await response.json();
  if (!response.ok) {
    throw new Error(extractError(data));
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

  if (response.status === 401) {
    handleUnauthorized();
    return;
  }

  const data = await response.json();
  if (!response.ok) {
    throw new Error(extractError(data));
  }
  return data;
}

// send a GET request with the auth token
async function get(url, token) {
  const response = await fetch(url, {
    headers: { 'Authorization': 'Bearer ' + token }
  });

  if (response.status === 401) {
    handleUnauthorized();
    return;
  }

  const data = await response.json();
  if (!response.ok) {
    throw new Error(extractError(data));
  }
  return data;
}

// show a red error alert
function showError(id, msg) {
  var el = document.getElementById(id);
  el.className = 'alert alert-danger';
  var text;
  if (!msg) {
    text = 'Something went wrong';
  } else if (typeof msg === 'string') {
    text = msg;
  } else if (msg.message) {
    // Error object or object with .message
    text = msg.message;
  } else if (Array.isArray(msg)) {
    // raw Pydantic detail array passed by mistake
    text = friendlyValidationMsg(msg[0]);
  } else {
    text = 'Something went wrong';
  }
  el.textContent = text;
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
