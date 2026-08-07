function showMessage(msg, type) {
  alert(msg);
}

function runApiCall() {
  var userId = document.getElementById('user-id').value;
  var scope = document.getElementById('scope').value;

  var results = {
    'name:legal':        { legal_name: 'Abdullah Mohammed Al-Harbi' },
    'name:preferred':    { preferred_name: 'Abdullah' },
    'name:professional': { professional_name: 'Dr. A. Al-Harbi' },
    'name:religious':    { religious_name: 'Abu Khalid' },
    'profile:basic':     { preferred_name: 'Abdullah', nationality: 'Saudi Arabian' }
  };

  var output = JSON.stringify({ user_id: userId, data: results[scope] }, null, 2);
  document.getElementById('api-result').textContent = output;
  document.getElementById('result-box').style.display = 'block';
}
