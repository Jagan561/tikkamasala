/**
 * Checkout flow.
 */
let _checkoutOrderId = null;
let _orderType = 'DELIVERY';

function setOrderType(type) {
  _orderType = type;
  const deliverySection = document.getElementById('delivery-section');
  const pickupNote = document.getElementById('pickup-note');
  const deliveryBtn = document.getElementById('type-delivery');
  const pickupBtn = document.getElementById('type-pickup');

  if (type === 'DELIVERY') {
    deliverySection && deliverySection.classList.remove('hidden');
    pickupNote && pickupNote.classList.add('hidden');
    deliveryBtn && deliveryBtn.classList.add('active');
    pickupBtn && pickupBtn.classList.remove('active');
  } else {
    deliverySection && deliverySection.classList.add('hidden');
    pickupNote && pickupNote.classList.remove('hidden');
    pickupBtn && pickupBtn.classList.add('active');
    deliveryBtn && deliveryBtn.classList.remove('active');
  }
}

async function handlePlaceOrder() {
  const btn = document.getElementById('place-order-btn');

  const payload = {
    order_type: _orderType,
    notes: document.getElementById('notes')?.value || '',
  };

  if (_orderType === 'DELIVERY') {
    const address = document.getElementById('delivery-address')?.value?.trim();
    const lat = parseFloat(document.getElementById('delivery-lat')?.value || '');
    const lng = parseFloat(document.getElementById('delivery-lng')?.value || '');

    if (!address) { showToast('Enter your delivery address.', 'warning'); return; }
    if (!lat || !lng) { showToast('Please use "Get My Location" to set coordinates.', 'warning'); return; }

    payload.delivery_address = address;
    payload.delivery_lat = lat;
    payload.delivery_lng = lng;
  }

  setLoading(btn, true, 'Placing order...');
  try {
    const order = await api.post('/api/orders', payload);
    _checkoutOrderId = order.order_id;
    showToast('Order created! Proceeding to payment...', 'success');
    // Store order ID and redirect to payment
    sessionStorage.setItem('pending_order_id', order.order_id);
    sessionStorage.setItem('pending_order_number', order.order_number);
    sessionStorage.setItem('pending_order_total', order.total);
    setTimeout(() => window.location.href = '/customer/payment.html', 800);
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    setLoading(btn, false, '🔒 Place Order & Pay');
  }
}

async function loadCheckoutSummary() {
  try {
    const cart = await api.get('/api/cart');
    const itemsEl = document.getElementById('checkout-items');
    const subtotalEl = document.getElementById('checkout-subtotal');
    const deliveryEl = document.getElementById('checkout-delivery');
    const totalEl = document.getElementById('checkout-total');

    if (itemsEl) {
      itemsEl.innerHTML = cart.items.map(item =>
        `<div style="display:flex;justify-content:space-between;padding:.3rem 0;font-size:.9rem">
          <span>${item.product_name} × ${item.quantity}</span>
          <span>${formatPrice(item.subtotal)}</span>
        </div>`
      ).join('');
    }
    if (subtotalEl) subtotalEl.textContent = formatPrice(cart.subtotal);
    if (deliveryEl) deliveryEl.textContent = _orderType === 'DELIVERY' ? '₹30' : '₹0';
    if (totalEl) {
      const total = cart.subtotal + (_orderType === 'DELIVERY' ? 30 : 0);
      totalEl.textContent = formatPrice(total);
    }
  } catch (err) {
    console.error('Checkout summary error:', err);
  }
}
