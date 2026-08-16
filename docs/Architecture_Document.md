# Smart Campus Canteen
## Architecture Document

**Tactive Assessment — Deliverable 4 (1 of 3)**

---

# 1. System Overview

The Smart Campus Canteen is a web-based ordering and inventory management system for a college canteen. Students browse a live menu, build a cart, and place orders against real-time stock. Admins manage the menu, monitor stock, and progress orders through their lifecycle.

Core capabilities:

- Student registration and login
- Session-based authentication and role-based authorization
- Menu browsing and search
- Cart management with server-enforced stock limits
- Order placement with server-trusted pricing and stock deduction
- Order history per student
- **Student-initiated order cancellation within a 5-minute grace window (new — Stage 3 feature)**
- Admin menu management (add / edit / price / stock / remove)
- Admin order status management

---

# 2. Architecture Diagram

```text
+------------------------------------------------------+
|                    User Browser                      |
|                                                        |
|       Student UI              Admin UI                |
|       HTML/Jinja              HTML/Jinja               |
|       CSS                     Vanilla JavaScript       |
+-------------------------+------------------------------+
                          |
                          | HTTP (form posts, redirects)
                          v
+------------------------------------------------------+
|                 Flask Web Application (app.py)        |
|                                                        |
|  Authentication   Page Routes   Admin Routes           |
|  (login_required, admin_required decorators)           |
+-------------------------+------------------------------+
                          |
                          v
+------------------------------------------------------+
|                  Service Layer                        |
|              services/order_service.py                |
|                                                        |
|   create_order_from_cart()   cancel_order()            |
|   Stock deduction/restoration, price authority,        |
|   ownership + status + time-window validation          |
+-------------------------+------------------------------+
                          |
                          v
+------------------------------------------------------+
|              SQLAlchemy ORM / Models (models.py)       |
|                                                        |
|      User      MenuItem      Order      OrderItem      |
+-------------------------+------------------------------+
                          |
                          v
+------------------------------------------------------+
|                     SQLite                            |
|                     canteen.db                        |
+------------------------------------------------------+
```

---

# 3. Presentation Layer

- **HTML + Jinja templates** render every page server-side; there is no client-side SPA framework.
- **CSS** (`static/css/style.css`) provides the visual design.
- **Vanilla JavaScript** (`static/js/app.js`) handles small progressive-enhancement behaviours (e.g. `data-confirm` confirmation dialogs on destructive actions like "Remove item" and "Cancel order").

Key pages: login, register, menu (with search), cart, order history, admin dashboard (menu + order management).

Client-side JavaScript is explicitly **not** the security boundary — every business rule enforced in the UI is re-checked on the server (see Section 6, Design document).

---

# 4. Backend Design

The Flask application (`app.py`) is responsible for:

1. Receiving HTTP requests (form posts, GET requests for pages).
2. Checking authentication (`@login_required`) and, where relevant, authorization (`@admin_required`).
3. Reading request form data.
4. Delegating business-rule validation and mutation to the service layer rather than embedding it in route handlers.
5. Committing or rolling back the database transaction based on the service layer's outcome.
6. Flashing a success/error message and redirecting (this app uses the classic server-rendered redirect-after-POST pattern, not a JSON API).

## 4.1 Service Layer

`services/order_service.py` centralizes order-related business logic so route handlers stay thin:

- `create_order_from_cart(user_id, cart_data)` — validates every cart line against current DB stock/availability, always uses the **current database price** (never anything the client could have supplied), deducts stock, and builds the `Order`/`OrderItem` rows.
- `cancel_order(order_id, user_id, now=None)` — **(new in Stage 3)** validates ownership, order status, and the 5-minute cancellation window, then restores stock and marks the order `Cancelled`.

Both functions raise `ValueError` with a human-readable message on any rule violation; the route layer catches this, rolls back, and flashes the message. Neither function commits the session itself — the caller (`app.py`) owns the transaction boundary, so a route can compose multiple service calls atomically if needed.

---

# 5. Data Layer

SQLAlchemy ORM models (`models.py`) map directly onto four tables in a single SQLite database file, `canteen.db`. See the Design document for the full schema and relationships.

---

# 6. Technology Choices and Why

| Choice | Why |
|---|---|
| **Flask** | Small surface area, explicit routing, no hidden magic — appropriate for a scoped assessment app where every request/response path needs to be auditable. |
| **SQLAlchemy + SQLite** | Zero external infrastructure to run the app or the test suite; SQLite is file-based, so an isolated test database is just a temp file, never the production `canteen.db`. |
| **Server-rendered Jinja, not a JS framework** | The app's interactions (add to cart, place order, admin CRUD) are simple form submissions; a full SPA would add build tooling and client-state complexity without a matching benefit, and would move business rules dangerously close to the client. |
| **Session-based auth (Flask's signed cookie session)** | Matches the server-rendered architecture; no token issuance/refresh complexity needed for a single-server deployment. |
| **Werkzeug password hashing** | Standard, already a Flask dependency, avoids reinventing password storage. |
| **A dedicated service layer for order logic** | Keeps stock/price/cancellation rules in one testable place instead of scattered across route handlers, which is also what made the Stage 3 feature addition low-risk — the route change was a few lines; the rule logic lived in one function. |

---

# 7. Deployment Design

- `Procfile` / `render.yaml` — configured for a Render.com-style PaaS deployment running `gunicorn app:app`.
- `requirements.txt` — pinned dependency versions (Flask 3.1.1, Flask-SQLAlchemy 3.1.1, SQLAlchemy 2.0.41, Werkzeug 3.1.3, gunicorn 23.0.0, pytest).
- `config.py` reads `DATABASE_URL` and `SECRET_KEY` from environment variables, falling back to a local SQLite file and a development-only default secret — the production secret key must be supplied via environment variable, never committed.
- This same environment-variable design is what makes the automated test suite safe: `tests/conftest.py` overrides `DATABASE_URL` to a throwaway file **before** `app.py`/`config.py` are imported, so tests can never write to the real `canteen.db`.

---

# 8. Security Design

- Passwords are hashed with Werkzeug (`generate_password_hash` / `check_password_hash`), never stored or logged in plain text.
- Every state-changing route that isn't public registration/login requires `@login_required`; every admin-only route additionally requires `@admin_required`.
- Server-side validation is authoritative for: menu item price/stock, cart quantity capping, order stock sufficiency, order price (always read fresh from the database, never trusted from the client), order ownership on cancellation, and order-status transitions (validated against an explicit allow-list).
- The order-cancellation feature added in Stage 3 follows the same pattern: ownership, status, and time-window checks all happen in `cancel_order()` on the server, and the "Cancel order" button's visibility in the template is UX only — the server re-validates independently of what the UI shows.

---

# 9. Project Structure

```text
smart-campus-canteen/
│
├── app.py
├── config.py
├── models.py
├── seed.py
├── requirements.txt
├── Procfile
├── render.yaml
├── README.md
│
├── services/
│   └── order_service.py
│
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── register.html
│   ├── menu.html
│   ├── cart.html
│   ├── orders.html
│   └── admin/
│       └── dashboard.html
│
├── static/
│   ├── css/style.css
│   └── js/app.js
│
└── tests/
    ├── conftest.py
    ├── test_auth.py
    ├── test_authorization.py
    ├── test_menu.py
    ├── test_cart.py
    ├── test_orders.py
    ├── test_admin.py
    └── test_order_cancellation.py   ← new, Stage 3
```

---

# 10. Conclusion

The architecture separates presentation (Jinja templates + minimal JS), request handling (Flask routes with auth/authz decorators), business rules (a dedicated order service), and persistence (SQLAlchemy over SQLite) into distinct layers. This separation is what allowed the Stage 3 feature — order cancellation — to be added as an isolated function in the service layer plus one thin route and one template change, without touching authentication, menu, or cart logic at all.
