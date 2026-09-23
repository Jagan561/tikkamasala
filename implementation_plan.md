# Tikka Masala Chat Corner — Full-Stack Implementation Plan

A complete production-structured chaat food ordering & delivery platform with customer auth, Razorpay payments, real-time WebSocket order tracking, admin dashboard, SMS OTP, 3 km delivery validation, and sales analytics.

---

## User Review Required

> [!IMPORTANT]
> **Razorpay Credentials**: You must provide your own `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET` (test mode credentials). The app ships with placeholder values in `.env.example`. Payments won't work until real test keys are added.

> [!IMPORTANT]
> **SMS OTP**: The app will use a **mock SMS provider** in `DEMO_MODE=true`. OTPs will be printed to the server console (and returned in the API response in dev mode) so the full flow can be demonstrated without a paid SMS account. When you're ready for production, plug in MSG91/Twilio credentials.

> [!IMPORTANT]
> **MySQL Required**: You need MySQL 8.x running locally. The backend auto-creates all tables via SQLAlchemy on startup. I'll include a one-liner setup command.

> [!WARNING]
> **AWS deployment is Phase 20** — This plan fully implements Phases 1–19 (local development + demo). AWS S3/RDS/EB architecture and config files will be included, but actual deployment is deferred as specified.

> [!NOTE]
> **No React/Next.js** — Frontend is pure HTML5 + CSS3 + Vanilla JS as required. The backend is Python FastAPI + SQLAlchemy + MySQL.

---

## Proposed Changes

### Phase 1 — Project Structure & Configuration

#### [NEW] Project scaffold (all directories + base files)

```
tikkamasala/
├── backend/
│   └── app/
│       ├── main.py
│       ├── config/
│       │   ├── settings.py
│       │   └── database.py
│       ├── models/       (13 model files)
│       ├── schemas/      (matching Pydantic schemas)
│       ├── routes/
│       │   ├── auth.py
│       │   ├── products.py
│       │   ├── categories.py
│       │   ├── cart.py
│       │   ├── orders.py
│       │   ├── payments.py
│       │   ├── delivery.py
│       │   ├── websocket.py
│       │   └── admin/
│       │       ├── dashboard.py
│       │       ├── orders.py
│       │       ├── products.py
│       │       ├── categories.py
│       │       ├── customers.py
│       │       ├── sales.py
│       │       └── inventory.py
│       ├── services/     (11 service files)
│       └── utils/
│           ├── security.py
│           ├── jwt.py
│           └── otp.py
├── frontend/
│   ├── index.html
│   ├── customer/         (11 HTML pages)
│   ├── admin/            (9 HTML pages)
│   ├── css/
│   │   ├── main.css
│   │   ├── customer.css
│   │   └── admin.css
│   └── js/               (10 JS files)
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

### Phase 2 — Database Schema (MySQL + SQLAlchemy)

#### [NEW] 13 database models

| Table | Key Fields |
|---|---|
| `users` | id, name, mobile, password_hash, is_verified, created_at |
| `admins` | id, username, password_hash, role |
| `categories` | id, name, description, is_active |
| `products` | id, name, description, price (DECIMAL), category_id, image_url, stock_quantity, is_available |
| `addresses` | id, user_id, label, address, lat, lng, is_default |
| `cart` | id, user_id (unique), created_at |
| `cart_items` | id, cart_id, product_id, quantity |
| `orders` | id, order_number, user_id, address_id, order_type, subtotal, delivery_fee, discount, total, status, delivery_otp, otp_expires_at |
| `order_items` | id, order_id, product_id, quantity, unit_price, subtotal |
| `payments` | id, order_id, razorpay_order_id, razorpay_payment_id, amount, currency, status |
| `otp` | id, mobile, code, purpose, expires_at, attempts, is_used |
| `inventory` | id, product_id (FK unique), current_stock, low_stock_threshold |
| `order_status_history` | id, order_id, status, changed_by, note, created_at |

All monetary fields use `DECIMAL(10,2)`. All tables have `created_at` + `updated_at`.

---

### Phase 3 — FastAPI Backend

#### [NEW] `backend/app/main.py`
- CORS middleware (configurable origins)
- Rate limiting (slowapi)
- Router registration (all route groups)
- WebSocket manager instantiation
- Startup: create DB tables + seed initial data

#### [NEW] `backend/app/config/settings.py`
- Pydantic `BaseSettings` loading from `.env`
- All env vars: DB URL, JWT secret, Razorpay keys, shop lat/lng, delivery radius, charge, SMS provider, AWS config, demo mode flag

#### [NEW] `backend/app/config/database.py`
- SQLAlchemy async engine + session factory
- `get_db` dependency

---

### Phase 4 — Authentication System

#### [NEW] `backend/app/routes/auth.py`
- `POST /api/auth/send-otp` — generate 6-digit OTP, store in DB, send via SMS service
- `POST /api/auth/verify-otp` — validate OTP, expire it, mark mobile as verified
- `POST /api/auth/register` — create user after OTP verification
- `POST /api/auth/login` — return JWT (customer role)
- `POST /api/auth/logout` — blacklist token
- `GET /api/auth/me` — return current user info

#### [NEW] `backend/app/utils/jwt.py`
- Create/decode JWT with role claim
- Token expiry configurable

#### [NEW] `backend/app/utils/security.py`
- bcrypt password hashing/verification

#### [NEW] `backend/app/services/sms_service.py`
- Abstract `SMSProvider` base class
- `MockSMSProvider` (prints to console, returns OTP in dev response)
- `MSG91Provider` stub (ready to wire up)
- Factory pattern: `get_sms_provider()` reads `SMS_PROVIDER` env var

#### [NEW] `backend/app/services/otp_service.py`
- OTP generation (secrets.randbelow)
- Store with expiry (10 min)
- Max 3 verify attempts
- 60s resend cooldown
- Cleanup expired OTPs

---

### Phase 5 — Product & Category APIs

#### [NEW] `backend/app/routes/products.py`
- `GET /api/products` — paginated, filter by category + availability
- `GET /api/products/{id}`

#### [NEW] `backend/app/routes/categories.py`
- `GET /api/categories`

---

### Phase 6 — Cart System

#### [NEW] `backend/app/routes/cart.py`
- `GET /api/cart` — user's cart with item totals
- `POST /api/cart/items` — add/update item (checks product availability + stock)
- `PATCH /api/cart/items/{id}` — update quantity
- `DELETE /api/cart/items/{id}` — remove item
- `DELETE /api/cart` — clear cart

Server-side price calculation — never trust frontend prices.

---

### Phase 7 — Order + Checkout System

#### [NEW] `backend/app/routes/orders.py`
- `POST /api/orders` — full order creation flow (12 steps per spec)
- `GET /api/orders` — customer's order list
- `GET /api/orders/{id}`

#### [NEW] `backend/app/services/order_service.py`
- Validate cart not empty
- Fetch real prices from DB
- Haversine distance check (3 km)
- Calculate delivery fee from config
- DB transaction: create order + items + payment record + Razorpay order

#### [NEW] `backend/app/utils/location.py`
- Haversine formula implementation

---

### Phase 8 — Razorpay Payment

#### [NEW] `backend/app/routes/payments.py`
- `POST /api/payments/create` — create Razorpay order, return order_id + key_id
- `POST /api/payments/verify` — verify HMAC-SHA256 signature, update payment + order status
- `POST /api/payments/webhook` — idempotent webhook handler (uses `razorpay_payment_id` as dedup key)

Signature verification uses `razorpay_order_id + "|" + razorpay_payment_id` + Razorpay key secret.

---

### Phase 9 — Delivery OTP

#### [NEW] `backend/app/routes/delivery.py`
- `POST /api/delivery-otp/send` — generate 6-digit OTP, send to customer SMS, store with expiry
- `POST /api/delivery-otp/verify` — verify OTP, update order to DELIVERED, emit WebSocket event

---

### Phase 10 — Admin APIs

#### [NEW] `backend/app/routes/admin/` (7 route files)

| Route | Operations |
|---|---|
| `dashboard.py` | GET stats: orders today, sales today, pending, preparing, completed, customers, low stock |
| `orders.py` | GET all orders, GET by ID, PATCH status |
| `products.py` | POST add, PUT edit, DELETE remove |
| `categories.py` | POST, PUT, DELETE |
| `customers.py` | GET customer list (no passwords) |
| `sales.py` | GET daily + monthly sales data for charts |
| `inventory.py` | GET inventory list, PATCH update stock |

All admin routes require `role == "admin"` JWT claim.

---

### Phase 11 — WebSocket Real-Time System

#### [NEW] `backend/app/services/websocket_manager.py`
- `ConnectionManager` class
- `connect(websocket, user_id, role)`
- `disconnect(websocket)`
- `send_to_user(user_id, message)` — customer-specific events
- `broadcast_to_admins(message)` — new order alerts

#### [NEW] `backend/app/routes/websocket.py`
- `WS /api/ws/orders?token=<jwt>` — authenticate on connect, add to manager

Events emitted:
- `NEW_ORDER` → all admins
- `ORDER_STATUS_CHANGED` → specific customer
- `ORDER_ACCEPTED`, `PREPARING`, `READY`, `OUT_FOR_DELIVERY`, `DELIVERED` → customer

---

### Phase 12 — Frontend (HTML/CSS/JS)

#### Customer Pages (11 files)
| Page | Key Features |
|---|---|
| `customer/login.html` | Mobile + password form, link to register |
| `customer/register.html` | Name + mobile + OTP flow + password |
| `customer/home.html` | Hero, popular items, categories, shop info |
| `customer/menu.html` | Cards from API, search + category filter |
| `customer/cart.html` | Item list, qty controls, server-calculated total |
| `customer/checkout.html` | Address, GPS location, order type, Razorpay |
| `customer/payment.html` | Razorpay checkout embed |
| `customer/order-success.html` | Confirmation, order ID, track button |
| `customer/track-order.html` | Visual timeline, real-time WS updates |
| `customer/my-orders.html` | Order history |
| `customer/profile.html` | Name, mobile, saved addresses |

#### Admin Pages (9 files)
| Page | Key Features |
|---|---|
| `admin/login.html` | Username + password |
| `admin/dashboard.html` | Stats cards, live new-order notifications |
| `admin/orders.html` | Full order table, status action buttons, OTP verify |
| `admin/products.html` | Product CRUD, image upload |
| `admin/categories.html` | Category CRUD |
| `admin/customers.html` | Customer list (no passwords) |
| `admin/inventory.html` | Stock levels, low-stock alerts |
| `admin/sales.html` | Bar/line charts (Chart.js) |
| `admin/reports.html` | Tabular reports by product/category/status |

#### CSS (3 files)
- `css/main.css` — Design tokens, typography (Google Fonts: Outfit), color palette (deep red, orange, golden, warm cream), utilities
- `css/customer.css` — Customer-specific components
- `css/admin.css` — Admin dashboard layout, data tables

#### JavaScript (10 files)
- `js/api.js` — Axios-like fetch wrapper, JWT header injection, error handling
- `js/auth.js` — Login, register, OTP flow, token management
- `js/products.js` — Menu load, search, filter
- `js/cart.js` — Add/remove/update, server-side totals
- `js/checkout.js` — Address form, GPS, order type toggle
- `js/location.js` — `navigator.geolocation` wrapper
- `js/payment.js` — Razorpay checkout flow, verify callback
- `js/orders.js` — Order list, order detail
- `js/websocket.js` — WS connect/reconnect, event dispatch
- `js/admin.js` — Dashboard, status update, OTP verify, charts

---

### Phase 13 — Seed Data & Demo Mode

#### [NEW] `backend/app/services/seed_service.py`
- 6 sample products (Pani Puri ₹50, Bhel Puri ₹60, Samosa ₹30, Masala Sandwich ₹80, Masala Dosa ₹90, Fresh Lime ₹40)
- Default admin account (username: `admin`, password: configurable via `.env`)
- 4 categories (Chaat, Snacks, Meals, Beverages)

---

### Phase 14 — Config & Deployment Prep

#### [NEW] `.env.example`
All 20+ env vars with clear documentation comments.

#### [NEW] `.gitignore`
Python + Node + OS ignores, always excludes `.env`.

#### [NEW] `requirements.txt`
```
fastapi
uvicorn[standard]
sqlalchemy
aiomysql
pymysql
pydantic-settings
python-jose[cryptography]
passlib[bcrypt]
razorpay
slowapi
python-multipart
boto3
python-dotenv
```

#### [NEW] `README.md`
Full setup guide: MySQL setup, Python venv, `.env` config, seeding, running, demo credentials, API docs link.

---

## Open Questions

> [!IMPORTANT]
> **Do you have a MySQL instance running locally?** If not, I can include Docker Compose setup as an alternative to install MySQL.

> [!IMPORTANT]
> **Razorpay Test Keys**: Do you have Razorpay test mode API keys? The payment flow will not complete without them. (Free to get at dashboard.razorpay.com)

> [!NOTE]
> **Shop Location**: What are the actual coordinates of Tikka Masala Chat Corner? I'll default to a placeholder (e.g., Chennai: 13.0827° N, 80.2707° E) that can be changed in `.env`.

> [!NOTE]
> **Admin Credentials**: I'll seed a default admin with `username: admin` / `password: Admin@123`. You can change this in `.env` before first run.

> [!NOTE]
> **Image Storage**: In demo mode, product images will use placeholder URLs (picsum.photos or similar). AWS S3 integration is wired but disabled behind the `USE_S3=false` flag.

---

## Verification Plan

### Automated Tests
- Run `uvicorn app.main:app --reload` and confirm all routes appear in `/docs`
- Verify DB tables created on startup
- Test OTP flow via `/docs` interactive API
- Test Razorpay test payment end-to-end

### Manual Verification (Critical Acceptance Test)
1. Register new customer → receive mock OTP in console → verify → login
2. Browse menu → add to cart → checkout → GPS location → PAY NOW (Razorpay test card `4111 1111 1111 1111`)
3. Backend verifies signature → order created → delivery OTP in console
4. Open admin panel in second browser → see real-time NEW ORDER notification (no refresh)
5. Admin changes status through all stages → customer tracking page updates in real-time (no refresh)
6. Admin enters delivery OTP → order marked DELIVERED
7. Sales dashboard reflects the order

### Build Verification
- `cd backend && pip install -r requirements.txt && python -m app.main` — must start without errors
- All 20 HTML pages load without 404
- All JS files load without console errors on initial page load
