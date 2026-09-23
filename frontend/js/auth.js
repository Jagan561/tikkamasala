/**
 * Authentication: register, OTP, login, logout.
 */

// ── Redirect guards ──────────────────────────────────────────
function requireCustomerAuth() {
  if (!api.getToken() || localStorage.getItem('tm_role') !== 'customer') {
    window.location.href = '/customer/login.html';
  }
}
function requireAdminAuth() {
  if (!api.getToken() || !['admin', 'superadmin'].includes(localStorage.getItem('tm_role'))) {
    window.location.href = '/admin/login.html';
  }
}
function redirectIfLoggedIn(role = 'customer') {
  if (api.getToken()) {
    if (role === 'admin') window.location.href = '/admin/dashboard.html';
    else window.location.href = '/customer/home.html';
  }
}

// ── Customer Login ───────────────────────────────────────────
async function handleCustomerLogin(e) {
  e.preventDefault();
  const btn = document.getElementById('login-btn');
  const errEl = document.getElementById('login-error');
  if (errEl) errEl.classList.add('hidden');
  setLoading(btn, true, 'Logging in...');
  try {
    const data = await api.post('/api/auth/login', {
      mobile: document.getElementById('mobile').value.trim(),
      password: document.getElementById('password').value,
    });
    api.setToken(data.access_token);
    localStorage.setItem('tm_user', JSON.stringify(data.user));
    localStorage.setItem('tm_role', 'customer');
    window.location.href = '/customer/home.html';
  } catch (err) {
    if (errEl) { errEl.textContent = err.message; errEl.classList.remove('hidden'); }
    else showToast(err.message, 'error');
  } finally {
    setLoading(btn, false, 'Login');
  }
}

// ── Admin Login ──────────────────────────────────────────────
async function handleAdminLogin(e) {
  e.preventDefault();
  const btn = document.getElementById('admin-login-btn');
  const errEl = document.getElementById('login-error');
  if (errEl) errEl.classList.add('hidden');
  setLoading(btn, true, 'Logging in...');
  try {
    const data = await api.post('/api/auth/admin/login', {
      username: document.getElementById('username').value.trim(),
      password: document.getElementById('password').value,
    });
    api.setToken(data.access_token);
    localStorage.setItem('tm_role', data.role);
    localStorage.setItem('tm_admin', JSON.stringify({ username: data.username, role: data.role }));
    window.location.href = '/admin/dashboard.html';
  } catch (err) {
    if (errEl) { errEl.textContent = err.message; errEl.classList.remove('hidden'); }
    else showToast(err.message, 'error');
  } finally {
    setLoading(btn, false, 'Login');
  }
}

// ── Send OTP ─────────────────────────────────────────────────
async function handleSendOTP(e) {
  e && e.preventDefault();
  const btn = document.getElementById('send-otp-btn');
  const mobile = document.getElementById('mobile').value.trim();
  if (!mobile) { showToast('Enter your mobile number.', 'warning'); return; }
  setLoading(btn, true, 'Sending...');
  try {
    const data = await api.post('/api/auth/send-otp', { mobile, purpose: 'REGISTRATION' });
    showToast('OTP sent! Check your mobile.', 'success');
    if (data.demo_otp) showToast(`Demo OTP: ${data.demo_otp}`, 'info', 10000);
    document.getElementById('otp-section').classList.remove('hidden');
    btn.textContent = 'Resend OTP';
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    setLoading(btn, false, 'Send OTP');
  }
}

// ── Verify OTP ────────────────────────────────────────────────
let _otpVerifiedToken = null;
async function handleVerifyOTP(e) {
  e && e.preventDefault();
  const btn = document.getElementById('verify-otp-btn');
  const mobile = document.getElementById('mobile').value.trim();
  const code = getOTPFromBoxes() || document.getElementById('otp-input')?.value.trim();
  if (!code || code.length !== 6) { showToast('Enter 6-digit OTP.', 'warning'); return; }
  setLoading(btn, true, 'Verifying...');
  try {
    const data = await api.post('/api/auth/verify-otp', { mobile, code, purpose: 'REGISTRATION' });
    _otpVerifiedToken = data.otp_verified_token;
    showToast('OTP verified!', 'success');
    document.getElementById('otp-section').classList.add('hidden');
    document.getElementById('password-section').classList.remove('hidden');
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    setLoading(btn, false, 'Verify OTP');
  }
}

// ── Register ──────────────────────────────────────────────────
async function handleRegister(e) {
  e && e.preventDefault();
  if (!_otpVerifiedToken) { showToast('Complete OTP verification first.', 'warning'); return; }
  const btn = document.getElementById('register-btn');
  setLoading(btn, true, 'Creating account...');
  try {
    const data = await api.post('/api/auth/register', {
      name: document.getElementById('name').value.trim(),
      mobile: document.getElementById('mobile').value.trim(),
      password: document.getElementById('password').value,
      confirm_password: document.getElementById('confirm-password').value,
      otp_verified_token: _otpVerifiedToken,
    });
    api.setToken(data.access_token);
    localStorage.setItem('tm_user', JSON.stringify(data.user));
    localStorage.setItem('tm_role', 'customer');
    showToast('Account created!', 'success');
    setTimeout(() => window.location.href = '/customer/home.html', 1000);
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    setLoading(btn, false, 'Create Account');
  }
}

// ── Logout ──────────────────────────────────────────────────
function logout(redirectTo = '/customer/login.html') {
  api.clearToken();
  window.location.href = redirectTo;
}

// ── OTP box helpers ──────────────────────────────────────────
function initOTPBoxes(containerSelector) {
  const boxes = document.querySelectorAll(containerSelector + ' .otp-box');
  boxes.forEach((box, i) => {
    box.addEventListener('input', () => {
      if (box.value.length > 1) box.value = box.value.slice(-1);
      if (box.value && boxes[i + 1]) boxes[i + 1].focus();
    });
    box.addEventListener('keydown', e => {
      if (e.key === 'Backspace' && !box.value && boxes[i - 1]) boxes[i - 1].focus();
    });
    box.addEventListener('paste', e => {
      const pasted = (e.clipboardData || window.clipboardData).getData('text').replace(/\D/g, '');
      boxes.forEach((b, idx) => { if (pasted[idx]) b.value = pasted[idx]; });
      e.preventDefault();
    });
  });
}

function getOTPFromBoxes() {
  const boxes = document.querySelectorAll('.otp-box');
  return [...boxes].map(b => b.value).join('');
}

// ── Get logged-in user ──────────────────────────────────────
function getUser() {
  try { return JSON.parse(localStorage.getItem('tm_user') || '{}'); } catch { return {}; }
}
function getAdminUser() {
  try { return JSON.parse(localStorage.getItem('tm_admin') || '{}'); } catch { return {}; }
}
