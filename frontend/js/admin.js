/**
 * Admin JavaScript — dashboard, orders, products, sales.
 */

// ── Dashboard ────────────────────────────────────────────────
async function loadDashboard() {
  try {
    const stats = await api.get('/api/admin/dashboard');
    setStatCard('stat-orders-today',    stats.orders_today);
    setStatCard('stat-sales-today',     '₹' + (stats.sales_today || 0).toLocaleString('en-IN'));
    setStatCard('stat-pending',         stats.pending_orders);
    setStatCard('stat-preparing',       stats.preparing_orders);
    setStatCard('stat-completed',       stats.completed_today);
    setStatCard('stat-customers',       stats.total_customers);
    setStatCard('stat-low-stock',       stats.low_stock_items);
  } catch (err) {
    console.error('Dashboard error:', err);
  }
}

function setStatCard(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

// ── Admin Orders ─────────────────────────────────────────────
async function loadAdminOrders() {
  const container = document.getElementById('admin-orders-table-body');
  if (!container) return;
  container.innerHTML = '<tr><td colspan="9" class="text-center text-muted">Loading...</td></tr>';
  try {
    const orders = await api.get('/api/admin/orders');
    if (!orders.length) {
      container.innerHTML = '<tr><td colspan="9" class="text-center text-muted">No orders yet.</td></tr>';
      return;
    }
    container.innerHTML = orders.map(o => `
      <tr>
        <td><strong>${o.order_number}</strong></td>
        <td>${o.customer_name}<br><small class="text-muted">${o.customer_mobile}</small></td>
        <td>${o.items.map(i => `${i.product_name} ×${i.quantity}`).join('<br>')}</td>
        <td><strong>${formatPrice(o.total)}</strong></td>
        <td><span class="badge badge-${o.payment_status === 'PAID' ? 'success' : 'warning'}">${o.payment_status}</span></td>
        <td><span class="badge badge-secondary">${o.order_type}</span></td>
        <td><span class="badge status-${o.status}">${o.status.replace(/_/g,' ')}</span></td>
        <td>${timeAgo(o.created_at)}</td>
        <td>
          <div class="actions">
            ${getStatusButtons(o.id, o.status)}
          </div>
        </td>
      </tr>
    `).join('');
  } catch (err) {
    container.innerHTML = `<tr><td colspan="9"><div class="alert alert-error">${err.message}</div></td></tr>`;
  }
}

function getStatusButtons(orderId, status) {
  const next = {
    'PAYMENT_VERIFIED': [['PREPARING','Start Preparing','btn-secondary'],['CANCELLED','Cancel','btn-ghost']],
    'PREPARING':        [['READY','Mark Ready','btn-accent']],
    'READY':            [['OUT_FOR_DELIVERY','Out for Delivery','btn-primary']],
    'OUT_FOR_DELIVERY': [['verify-otp','Verify OTP 🔑','btn-success']],
  };
  const actions = next[status] || [];
  return actions.map(([s, label, cls]) => {
    if (s === 'verify-otp') {
      return `<button class="btn ${cls} btn-sm" onclick="openOTPModal(${orderId})">🔑 Verify OTP</button>`;
    }
    return `<button class="btn ${cls} btn-sm" onclick="updateOrderStatus(${orderId},'${s}')">${label}</button>`;
  }).join('');
}

async function updateOrderStatus(orderId, status) {
  try {
    await api.patch(`/api/admin/orders/${orderId}/status`, { status });
    showToast(`Order updated to ${status}`, 'success');
    loadAdminOrders();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// ── OTP Modal ───────────────────────────────────────────────
function openOTPModal(orderId) {
  const modal = document.getElementById('otp-modal');
  if (modal) {
    modal.classList.remove('hidden');
    document.getElementById('otp-order-id').value = orderId;
    document.getElementById('delivery-otp-input').value = '';
    document.getElementById('delivery-otp-input').focus();
  }
}
function closeOTPModal() {
  const modal = document.getElementById('otp-modal');
  if (modal) modal.classList.add('hidden');
}
async function verifyDeliveryOTP() {
  const orderId = parseInt(document.getElementById('otp-order-id').value);
  const otp = document.getElementById('delivery-otp-input').value.trim();
  if (!otp || otp.length !== 6) { showToast('Enter 6-digit OTP.', 'warning'); return; }
  const btn = document.getElementById('verify-otp-btn');
  setLoading(btn, true, 'Verifying...');
  try {
    await api.post('/api/delivery-otp/verify', { order_id: orderId, otp });
    showToast('Order marked as DELIVERED! 🎉', 'success');
    closeOTPModal();
    loadAdminOrders();
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    setLoading(btn, false, 'Verify & Deliver');
  }
}

// ── Admin Products ───────────────────────────────────────────
async function loadAdminProducts() {
  const container = document.getElementById('admin-products-body');
  if (!container) return;
  try {
    const products = await api.get('/api/products');
    const categories = await api.get('/api/categories');
    const catMap = {};
    categories.forEach(c => catMap[c.id] = c.name);

    container.innerHTML = products.map(p => `
      <tr>
        <td><img src="${p.image_url || ''}" style="width:48px;height:48px;object-fit:cover;border-radius:8px;background:var(--bg)"></td>
        <td><strong>${p.name}</strong></td>
        <td>${catMap[p.category_id] || '—'}</td>
        <td>${formatPrice(p.price)}</td>
        <td>${p.stock_quantity}</td>
        <td><span class="badge badge-${p.is_available ? 'success' : 'error'}">${p.is_available ? 'Available' : 'Unavailable'}</span></td>
        <td>
          <div class="actions">
            <button class="btn btn-outline btn-sm" onclick="editProduct(${p.id})">Edit</button>
            <button class="btn btn-ghost btn-sm" style="color:var(--error)" onclick="deleteProduct(${p.id})">Delete</button>
          </div>
        </td>
      </tr>
    `).join('');
  } catch (err) {
    container.innerHTML = `<tr><td colspan="7"><div class="alert alert-error">${err.message}</div></td></tr>`;
  }
}

async function deleteProduct(id) {
  if (!confirm('Delete this product?')) return;
  try {
    await api.del(`/api/admin/products/${id}`);
    showToast('Product deleted.', 'success');
    loadAdminProducts();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function saveProduct(event) {
  event.preventDefault();
  const id = document.getElementById('product-id')?.value;
  const payload = {
    name: document.getElementById('p-name').value,
    description: document.getElementById('p-desc').value,
    price: parseFloat(document.getElementById('p-price').value),
    category_id: parseInt(document.getElementById('p-cat').value) || null,
    image_url: document.getElementById('p-img').value,
    stock_quantity: parseInt(document.getElementById('p-stock').value) || 100,
    is_available: document.getElementById('p-available').checked,
    is_featured: document.getElementById('p-featured').checked,
  };
  const btn = document.getElementById('save-product-btn');
  setLoading(btn, true, 'Saving...');
  try {
    if (id) {
      await api.put(`/api/admin/products/${id}`, payload);
      showToast('Product updated.', 'success');
    } else {
      await api.post('/api/admin/products', payload);
      showToast('Product created.', 'success');
    }
    closeProductModal();
    loadAdminProducts();
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    setLoading(btn, false, 'Save Product');
  }
}

function openProductModal(product = null) {
  document.getElementById('product-modal').classList.remove('hidden');
  document.getElementById('product-form').reset();
  if (product) {
    document.getElementById('product-modal-title').textContent = 'Edit Product';
    document.getElementById('product-id').value = product.id;
    document.getElementById('p-name').value = product.name;
    document.getElementById('p-desc').value = product.description || '';
    document.getElementById('p-price').value = product.price;
    document.getElementById('p-stock').value = product.stock_quantity;
    document.getElementById('p-img').value = product.image_url || '';
    document.getElementById('p-available').checked = product.is_available;
    document.getElementById('p-featured').checked = product.is_featured;
  } else {
    document.getElementById('product-modal-title').textContent = 'Add Product';
    document.getElementById('product-id').value = '';
  }
}
function closeProductModal() {
  document.getElementById('product-modal').classList.add('hidden');
}

async function editProduct(id) {
  try {
    const product = await api.get(`/api/products/${id}`);
    openProductModal(product);
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// ── Sales Charts ─────────────────────────────────────────────
async function loadSalesCharts() {
  try {
    const [daily, monthly, summary] = await Promise.all([
      api.get('/api/admin/sales/daily?days=7'),
      api.get('/api/admin/sales/monthly?months=6'),
      api.get('/api/admin/sales/summary'),
    ]);

    // Update summary cards
    if (document.getElementById('today-orders')) {
      document.getElementById('today-orders').textContent = summary.today.orders;
      document.getElementById('today-revenue').textContent = formatPrice(summary.today.revenue);
      document.getElementById('month-orders').textContent = summary.this_month.orders;
      document.getElementById('month-revenue').textContent = formatPrice(summary.this_month.revenue);
    }

    // Daily chart
    const dailyCtx = document.getElementById('daily-chart');
    if (dailyCtx && typeof Chart !== 'undefined') {
      new Chart(dailyCtx, {
        type: 'bar',
        data: {
          labels: daily.map(d => d.date),
          datasets: [
            { label: 'Revenue (₹)', data: daily.map(d => d.revenue), backgroundColor: 'rgba(200,16,46,.75)', borderRadius: 6 },
            { label: 'Orders', data: daily.map(d => d.orders), backgroundColor: 'rgba(232,119,34,.75)', borderRadius: 6 },
          ]
        },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'top' } } }
      });
    }

    // Monthly chart
    const monthlyCtx = document.getElementById('monthly-chart');
    if (monthlyCtx && typeof Chart !== 'undefined') {
      const labels = monthly.map(m => `${m.year}-${String(m.month).padStart(2,'0')}`);
      new Chart(monthlyCtx, {
        type: 'line',
        data: {
          labels,
          datasets: [
            { label: 'Revenue (₹)', data: monthly.map(m => m.revenue), borderColor: '#C8102E', backgroundColor: 'rgba(200,16,46,.1)', fill: true, tension: .4 },
          ]
        },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'top' } } }
      });
    }
  } catch (err) {
    console.error('Sales charts error:', err);
  }
}

// ── Admin Navigation ─────────────────────────────────────────
function initAdminNav() {
  // Highlight active link
  const path = window.location.pathname;
  document.querySelectorAll('.sidebar-link').forEach(link => {
    if (link.getAttribute('href') && path.endsWith(link.getAttribute('href').split('/').pop())) {
      link.classList.add('active');
    }
  });

  // Sidebar toggle for mobile
  const toggleBtn = document.getElementById('sidebar-toggle');
  const sidebar = document.querySelector('.sidebar');
  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener('click', () => {
      const isOpen = sidebar.classList.toggle('open');
      const overlay = document.getElementById('sidebar-overlay');
      if (overlay) overlay.classList.toggle('active', isOpen);
    });
  }

  // Admin username display
  const admin = getAdminUser();
  document.querySelectorAll('.admin-username').forEach(el => el.textContent = admin.username || 'Admin');

  // Logout
  document.querySelectorAll('.admin-logout').forEach(btn => {
    btn.addEventListener('click', () => logout('/admin/login.html'));
  });
}
// Close sidebar (called by overlay click)
function closeSidebar() {
  const sidebar = document.querySelector('.sidebar');
  const overlay = document.getElementById('sidebar-overlay');
  if (sidebar) sidebar.classList.remove('open');
  if (overlay) overlay.classList.remove('active');
}


function initAdminWebSocket() {
  wsConnect();
  wsOn('NEW_ORDER', handleNewOrderNotification);
  wsOn('ORDER_UPDATED', () => { if (typeof loadAdminOrders === 'function') loadAdminOrders(); });
}

function handleNewOrderNotification(data) {
  const order = data.order || data;
  const badge = document.getElementById('notification-badge');
  if (badge) {
    badge.classList.remove('hidden');
    badge.textContent = parseInt(badge.textContent || '0') + 1;
  }

  // Play notification sound
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const oscillator = ctx.createOscillator();
    const gainNode = ctx.createGain();
    oscillator.connect(gainNode);
    gainNode.connect(ctx.destination);
    oscillator.frequency.value = 880;
    gainNode.gain.setValueAtTime(0.3, ctx.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.5);
    oscillator.start(ctx.currentTime);
    oscillator.stop(ctx.currentTime + 0.5);
  } catch (e) {}

  // Show notification card
  const notifContainer = document.getElementById('notifications-container');
  if (notifContainer) {
    const items = order.items || [];
    notifContainer.insertAdjacentHTML('afterbegin', `
      <div class="new-order-notification" id="notif-${order.id}">
        <div class="notification-header">
          <span class="notification-bell">🔔</span>
          <span class="notification-title">NEW ORDER — ${order.order_number}</span>
        </div>
        <div style="font-size:.9rem;color:var(--text-muted)">
          ${items.map(i => `${i.name} ×${i.quantity}`).join(', ')}
        </div>
        <div style="font-weight:700;color:var(--primary);margin-top:.5rem">${formatPrice(order.total)}</div>
        <div class="notification-actions">
          <button class="btn btn-secondary btn-sm" onclick="updateOrderStatus(${order.id},'PREPARING');document.getElementById('notif-${order.id}').remove()">🍽️ Start Preparing</button>
          <button class="btn btn-ghost btn-sm" onclick="document.getElementById('notif-${order.id}').remove()">Dismiss</button>
        </div>
      </div>
    `);
    if (typeof loadAdminOrders === 'function') setTimeout(loadAdminOrders, 500);
  }
  showToast(`New Order: ${order.order_number} — ${formatPrice(order.total)}`, 'info', 8000);
}
