/**
 * Shared customer header + dark mobile sidebar.
 * One implementation for every customer page — do not duplicate per page.
 */
(function () {
  const NAV_ITEMS = [
    { href: '/customer/home.html', icon: '🏠', label: 'Home', match: ['/customer/home.html', '/customer/'] },
    { href: '/customer/menu.html', icon: '🍽️', label: 'Menu', match: ['/customer/menu.html'] },
    { href: '/customer/my-orders.html', icon: '📋', label: 'My Orders', match: ['/customer/my-orders.html', '/customer/track-order.html'] },
    { href: '/customer/cart.html', icon: '🛒', label: 'Cart', match: ['/customer/cart.html', '/customer/checkout.html', '/customer/payment.html'], badge: true },
    { href: '/customer/profile.html', icon: '👤', label: 'Profile', match: ['/customer/profile.html'] },
  ];

  const LOGO_MARK = '🫙';

  function currentPath() {
    return window.location.pathname || '';
  }

  function isActive(item) {
    const path = currentPath();
    return item.match.some((m) => path === m || path.endsWith(m));
  }

  function isOpen() {
    const sidebar = document.getElementById('customer-sidebar');
    return !!(sidebar && sidebar.classList.contains('open'));
  }

  function setOpen(open) {
    const sidebar = document.getElementById('customer-sidebar');
    const overlay = document.getElementById('customer-nav-overlay');
    const burger = document.getElementById('hamburger');
    if (sidebar) sidebar.classList.toggle('open', open);
    if (overlay) overlay.classList.toggle('active', open);
    if (burger) {
      burger.classList.toggle('open', open);
      burger.setAttribute('aria-expanded', open ? 'true' : 'false');
    }
    document.body.classList.toggle('customer-nav-open', open);
  }

  function closeCustomerNav() {
    setOpen(false);
  }

  function toggleNav(e) {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }
    setOpen(!isOpen());
  }

  function renderMarkup() {
    const path = currentPath();
    const links = NAV_ITEMS.map((item) => {
      const active = isActive(item) ? ' active' : '';
      const badge = item.badge
        ? '<span class="badge-count cart-badge hidden">0</span>'
        : '';
      return `<a href="${item.href}" class="customer-sidebar-link${active}" data-nav-item>
        <span class="link-icon">${item.icon}</span>
        <span>${item.label}</span>
        ${badge}
      </a>`;
    }).join('');

    return {
      header: `
        <a href="/customer/home.html" class="navbar-brand">
          <div class="navbar-logo" aria-hidden="true">${LOGO_MARK}</div>
          <div class="navbar-brand-text">
            <span class="brand-full">TIKKA MASALA CHAT CORNER</span>
            <span class="brand-short">TIKKA MASALA</span>
          </div>
        </a>
        <button type="button" class="hamburger" id="hamburger" aria-label="Open menu" aria-expanded="false" aria-controls="customer-sidebar">
          <span></span><span></span><span></span>
        </button>
      `,
      sidebar: `
        <div class="customer-sidebar-brand">
          <div class="sidebar-logo-icon">${LOGO_MARK}</div>
          <div>
            <div class="customer-sidebar-tmcc">TMCC</div>
            <div class="customer-sidebar-full">TIKKA MASALA CHAT CORNER</div>
            <div class="customer-sidebar-panel">CUSTOMER PANEL</div>
          </div>
        </div>
        <nav class="customer-sidebar-nav">${links}</nav>
      `,
      footer: `
        <footer class="tmcc-footer">
          <div class="container">
            <div class="tmcc-footer-brand">
              <div class="tmcc-footer-logo">${LOGO_MARK}</div>
              <div>
                <div class="tmcc-footer-tmcc">TMCC</div>
                <div class="tmcc-footer-name">TIKKA MASALA CHAT CORNER</div>
              </div>
            </div>
            <div class="tmcc-footer-grid">
              <div>
                <div class="tmcc-footer-label">Phone / WhatsApp</div>
                <a href="tel:8667246511">86672 46511</a>
                <a href="https://wa.me/918667246511" target="_blank" rel="noopener">Chat on WhatsApp</a>
              </div>
              <div>
                <div class="tmcc-footer-label">Timing</div>
                <p>3 PM - 2 AM (Midnight)</p>
                <p>Open All Days</p>
              </div>
              <div>
                <div class="tmcc-footer-label">Info</div>
                <p>Parcel Charges: ₹10 Extra</p>
                <p>Jain Food Available</p>
                <a href="https://instagram.com/tikkamasalachatcorner" target="_blank" rel="noopener">Instagram: @tikkamasalachatcorner</a>
              </div>
            </div>
          </div>
        </footer>
      `,
      path,
    };
  }

  function mount() {
    if (document.body.classList.contains('no-customer-nav')) return;

    const { header, sidebar, footer } = renderMarkup();

    let navbar = document.querySelector('.navbar');
    if (!navbar) {
      navbar = document.createElement('nav');
      navbar.className = 'navbar';
      document.body.prepend(navbar);
    }
    navbar.innerHTML = header;

    let overlay = document.getElementById('customer-nav-overlay');
    if (!overlay) {
      overlay = document.createElement('div');
      overlay.id = 'customer-nav-overlay';
      overlay.className = 'customer-nav-overlay';
      document.body.appendChild(overlay);
    }

    let aside = document.getElementById('customer-sidebar');
    if (aside) aside.remove();
    aside = document.createElement('aside');
    aside.id = 'customer-sidebar';
    aside.className = 'customer-sidebar';
    aside.setAttribute('aria-hidden', 'true');
    aside.innerHTML = sidebar;
    document.body.appendChild(aside);

    if (!document.querySelector('.tmcc-footer')) {
      document.body.insertAdjacentHTML('beforeend', footer);
    }

    bindEvents(navbar, overlay, aside);

    if (typeof loadCart === 'function') {
      loadCart();
    }
  }

  function bindEvents(navbar, overlay, aside) {
    const burger = document.getElementById('hamburger');
    if (burger && burger.dataset.navBound !== '1') {
      burger.dataset.navBound = '1';
      burger.addEventListener('click', toggleNav);
    }

    if (overlay && overlay.dataset.navBound !== '1') {
      overlay.dataset.navBound = '1';
      overlay.addEventListener('click', closeCustomerNav);
    }

    if (aside && aside.dataset.navBound !== '1') {
      aside.dataset.navBound = '1';
      aside.addEventListener('click', (e) => {
        const link = e.target.closest('[data-nav-item]');
        if (link) closeCustomerNav();
      });
    }

    if (!document.documentElement.dataset.tmNavEscape) {
      document.documentElement.dataset.tmNavEscape = '1';
      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeCustomerNav();
      });
    }
  }

  function initCustomerNav() {
    mount();
  }

  window.toggleNav = toggleNav;
  window.closeCustomerNav = closeCustomerNav;
  window.initCustomerNav = initCustomerNav;

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initCustomerNav);
  } else {
    initCustomerNav();
  }
})();
