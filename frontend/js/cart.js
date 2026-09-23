/**
 * Cart management — all prices come from the server.
 */
let _cart = { id: null, items: [], subtotal: 0, item_count: 0 };

async function loadCart() {
  try {
    _cart = await api.get('/api/cart');
    updateCartUI();
    updateCartBadge();
    return _cart;
  } catch (err) {
    console.error('Cart load error:', err);
    return _cart;
  }
}

async function addToCart(productId, quantity = 1) {
  try {
    _cart = await api.post('/api/cart/items', { product_id: productId, quantity });
    updateCartUI();
    updateCartBadge();
    showToast('Added to cart!', 'success');
    return true;
  } catch (err) {
    showToast(err.message, 'error');
    return false;
  }
}

async function updateCartItem(itemId, quantity) {
  try {
    _cart = await api.patch(`/api/cart/items/${itemId}`, { quantity });
    updateCartUI();
    updateCartBadge();
    return true;
  } catch (err) {
    showToast(err.message, 'error');
    return false;
  }
}

async function removeCartItem(itemId) {
  try {
    _cart = await api.del(`/api/cart/items/${itemId}`);
    updateCartUI();
    updateCartBadge();
    return true;
  } catch (err) {
    showToast(err.message, 'error');
    return false;
  }
}

async function clearCart() {
  try {
    await api.del('/api/cart');
    _cart = { id: null, items: [], subtotal: 0, item_count: 0 };
    updateCartUI();
    updateCartBadge();
    return true;
  } catch (err) {
    showToast(err.message, 'error');
    return false;
  }
}

function updateCartBadge() {
  document.querySelectorAll('.cart-badge').forEach(el => {
    el.textContent = _cart.item_count || 0;
    if (_cart.item_count > 0) el.classList.remove('hidden');
    else el.classList.add('hidden');
  });
}

function updateCartUI() {
  // cart.html specific
  const listEl = document.getElementById('cart-items-list');
  const emptyEl = document.getElementById('cart-empty');
  const summaryEl = document.getElementById('cart-summary');

  if (!listEl) return;

  if (!_cart.items || _cart.items.length === 0) {
    listEl.innerHTML = '';
    emptyEl && emptyEl.classList.remove('hidden');
    summaryEl && summaryEl.classList.add('hidden');
    return;
  }
  emptyEl && emptyEl.classList.add('hidden');
  summaryEl && summaryEl.classList.remove('hidden');

  listEl.innerHTML = _cart.items.map(item => `
    <div class="cart-item" data-item-id="${item.id}">
      <img class="cart-item-img" src="${item.product_image || 'https://images.unsplash.com/photo-1601050690597-df0568f70950?w=150'}" alt="${item.product_name}" loading="lazy">
      <div>
        <div class="cart-item-name">${item.product_name}</div>
        <div class="cart-item-price">${formatPrice(item.unit_price)} each</div>
        <div class="qty-control" style="margin-top:.5rem;display:inline-flex;">
          <button class="qty-btn" onclick="changeQty(${item.id}, ${item.quantity - 1})">−</button>
          <span class="qty-val">${item.quantity}</span>
          <button class="qty-btn" onclick="changeQty(${item.id}, ${item.quantity + 1})">+</button>
        </div>
      </div>
      <div class="cart-item-actions">
        <div class="cart-item-subtotal">${formatPrice(item.subtotal)}</div>
        <button class="cart-remove-btn" onclick="removeItem(${item.id})">🗑 Remove</button>
      </div>
    </div>
  `).join('');

  // Update summary
  const deliveryFee = 30; // preview — actual is server-computed at checkout
  document.getElementById('summary-subtotal').textContent = formatPrice(_cart.subtotal);
  document.getElementById('summary-items').textContent = _cart.item_count + ' item(s)';
}

async function changeQty(itemId, qty) {
  if (qty < 1) {
    if (confirm('Remove this item from cart?')) await removeCartItem(itemId);
    return;
  }
  await updateCartItem(itemId, qty);
}

async function removeItem(itemId) {
  await removeCartItem(itemId);
}
