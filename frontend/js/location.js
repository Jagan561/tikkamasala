/**
 * Geolocation + coordinates display.
 */
let _currentLocation = null;

async function getCurrentLocation() {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error('Geolocation not supported by your browser.'));
      return;
    }
    navigator.geolocation.getCurrentPosition(
      pos => {
        _currentLocation = { lat: pos.coords.latitude, lng: pos.coords.longitude };
        resolve(_currentLocation);
      },
      err => {
        const msgs = {
          1: 'Location permission denied. Please allow location access.',
          2: 'Location unavailable.',
          3: 'Location request timed out.',
        };
        reject(new Error(msgs[err.code] || 'Location error.'));
      },
      { timeout: 10000, enableHighAccuracy: true }
    );
  });
}

async function handleGetLocation() {
  const btn = document.getElementById('location-btn');
  const statusEl = document.getElementById('location-status');
  setLoading(btn, true, 'Getting location...');
  try {
    const loc = await getCurrentLocation();
    _currentLocation = loc;
    if (statusEl) {
      statusEl.innerHTML = `<span style="color:var(--success)">📍 Location detected: ${loc.lat.toFixed(5)}, ${loc.lng.toFixed(5)}</span>`;
    }
    // Fill hidden fields
    const latEl = document.getElementById('delivery-lat');
    const lngEl = document.getElementById('delivery-lng');
    if (latEl) latEl.value = loc.lat;
    if (lngEl) lngEl.value = loc.lng;
    showToast('Location captured!', 'success');
  } catch (err) {
    showToast(err.message, 'error');
    if (statusEl) statusEl.innerHTML = `<span style="color:var(--error)">⚠️ ${err.message}</span>`;
  } finally {
    setLoading(btn, false, '📍 Use My Current Location');
  }
}

function getLocation() { return _currentLocation; }
