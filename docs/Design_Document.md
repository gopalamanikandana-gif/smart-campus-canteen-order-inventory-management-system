# Smart Campus Canteen
## Design Document

**Tactive Assessment — Deliverable 4 (2 of 3)**

---

# 1. Data Model

## 1.1 User

```text
User
----
id              INTEGER PK
name            VARCHAR(100)  NOT NULL
email           VARCHAR(150)  NOT NULL, UNIQUE, INDEXED
password_hash   VARCHAR(255)  NOT NULL
role            VARCHAR(20)   NOT NULL, DEFAULT 'student'   ("student" | "admin")
```

Self-registration (`POST /register`) always creates a `student`. Admin accounts are seeded/created out-of-band (`seed.py`), never through the public registration form.

## 1.2 MenuItem

```text
MenuItem
--------
id              INTEGER PK
name            VARCHAR(120)  NOT NULL
description     TEXT          DEFAULT ''
category        VARCHAR(80)   NOT NULL, DEFAULT 'General'
price           FLOAT         NOT NULL
stock           INTEGER       NOT NULL, DEFAULT 0
is_available    BOOLEAN       NOT NULL, DEFAULT True
```

`is_available` and `stock` are related but distinct: an admin can explicitly mark an item unavailable (e.g. seasonal removal) independent of stock count, and the system also auto-flips `is_available = False` when `stock` reaches `0`, and back to `True` if stock is restored (including by the Stage 3 cancellation feature).

## 1.3 Order

```text
Order
-----
id              INTEGER PK
user_id         INTEGER FK -> User.id, NOT NULL
total           FLOAT   NOT NULL, DEFAULT 0
status          VARCHAR(30) NOT NULL, DEFAULT 'Pending'
                ("Pending" | "Preparing" | "Ready" | "Completed" | "Cancelled")
created_at      DATETIME NOT NULL, DEFAULT utcnow()
```

## 1.4 OrderItem

```text
OrderItem
---------
id              INTEGER PK
order_id        INTEGER FK -> Order.id, NOT NULL
menu_item_id    INTEGER FK -> MenuItem.id, NULLABLE
item_name       VARCHAR(120) NOT NULL
unit_price      FLOAT NOT NULL
quantity        INTEGER NOT NULL
subtotal        FLOAT NOT NULL
```

`item_name` and `unit_price` are captured as a **snapshot at order time**, not looked up live — so an order's receipt stays accurate even if the menu item is later renamed, repriced, or removed. `menu_item_id` is nullable specifically to allow the original `MenuItem` to be deleted later without breaking historical orders (though the current admin "remove" action soft-deactivates rather than hard-deletes).

## 1.5 Relationships

```text
User        1 -------- * Order
Order       1 -------- * OrderItem
MenuItem    1 -------- * OrderItem   (nullable FK — see above)
```

---

# 2. Key Flows

## 2.1 Place Order

```text
Student
  |
  v
Add items to cart (session-stored: {menu_item_id: quantity})
  |
  v
POST /orders/place
  |
  v
services.order_service.create_order_from_cart(user_id, cart)
  |
  +-- For each cart line:
  |     - item exists and is_available?          -> else reject
  |     - item.stock >= requested quantity?       -> else reject
  |     - unit_price = current MenuItem.price     (never client-supplied)
  |     - item.stock -= quantity
  |     - item.is_available = item.stock > 0
  |
  v
Order + OrderItem rows created, total computed server-side
  |
  v
db.session.commit()  (owned by the route, not the service function)
  |
  v
Cart cleared, redirect to order history
```

## 2.2 Cancel Order — new in Stage 3

```text
Student (on Order History page, "Cancel order" button — shown only for Pending orders)
  |
  v
POST /orders/<id>/cancel
  |
  v
services.order_service.cancel_order(order_id, user_id, now=utcnow())
  |
  +-- order exists AND belongs to this user?     -> else "Order not found."
  +-- order.status == "Pending"?                 -> else "This order can no longer be cancelled."
  +-- now - order.created_at <= 5 minutes?        -> else "The cancellation window has expired."
  |
  v
For each OrderItem with a live menu_item_id:
  MenuItem.stock += quantity
  MenuItem.is_available = True (if stock now > 0)
  |
  v
order.status = "Cancelled"
  |
  v
db.session.commit(), flash success, redirect to order history
```

Design notes on the cancellation rule:

- **Why "Order not found." rather than "Not your order."** for the ownership failure — this avoids confirming to a student that *an* order with that ID exists at all, which is a minor information-leak reduction consistent with how the rest of the app avoids revealing details about other users' data.
- **Why a `now` parameter on `cancel_order()`** — the 5-minute window is time-dependent, so the function accepts an injectable "current time" for deterministic testing (`tests/test_order_cancellation.py::test_cancel_after_window_expired_is_rejected` calls it directly with a simulated timestamp 10 minutes after order placement) instead of requiring the test to sleep for 5 real minutes or monkeypatch the global `datetime` module.
- **Why status must still be `Pending`** — once an admin has moved an order to `Preparing`, the canteen has already started acting on it; allowing cancellation past that point would let a student cancel food that's already being made, which is a real-world business rule, not just a data-integrity one.

## 2.3 Admin Order Status Update

```text
Admin
  |
  v
POST /admin/orders/<id>/status  { status: "Preparing" | "Ready" | "Completed" | "Cancelled" }
  |
  v
status validated against an explicit allow-list
  |
  v
order.status updated, commit, flash, redirect to admin dashboard
```

Note: an admin can independently set an order to `Cancelled` at any time (no time window, no ownership check — admin authority is broader by design), whereas a student can only self-cancel through the narrower `cancel_order()` path with its window/status guard.

---

# 3. Interface Design

The application is server-rendered; there is no separate JSON API. Routes are grouped below by area.

## Authentication
```text
GET/POST  /register
GET/POST  /login
GET       /logout
```

## Menu
```text
GET  /menu            (supports ?q=<search term>)
```

## Cart (session-stored, per logged-in user)
```text
POST  /cart/add/<item_id>
POST  /cart/update     (form: qty_<item_id>=<n> per line)
POST  /cart/remove/<item_id>
GET   /cart
```

## Orders
```text
POST  /orders/place
GET   /orders
POST  /orders/<order_id>/cancel      ← new in Stage 3
```

## Admin
```text
GET   /admin
POST  /admin/items/add
POST  /admin/items/<id>/edit
POST  /admin/items/<id>/delete
POST  /admin/orders/<id>/status
```

---

# 4. Error Handling

The application uses Flask's flash-message + redirect pattern rather than JSON error bodies, matching its server-rendered UI. Representative error conditions:

```text
Invalid registration data          -> "Enter a valid name/email." / "Password must be at least 6 characters."
Duplicate email registration       -> "Email is already registered."
Invalid login                      -> "Invalid email or password."
Unauthenticated access             -> redirect to /login
Non-admin accessing admin route    -> "Admin access required." + redirect
Adding an unavailable item to cart -> "Menu item is unavailable."
Adding an out-of-stock item        -> "This item is out of stock."
Cart quantity exceeding stock      -> capped to available stock (not rejected outright), with a flash notice
Placing an order with empty cart   -> "Your cart is empty."
Insufficient stock at order time   -> "Not enough stock for <item>. Available: <n>."
Cancelling someone else's order    -> "Order not found."
Cancelling a non-Pending order     -> "This order can no longer be cancelled."      ← new, Stage 3
Cancelling after the time window   -> "The cancellation window has expired."        ← new, Stage 3
Invalid admin price/stock input    -> "Enter valid item details." / "Price and stock must be valid numbers."
Invalid order status update        -> "Invalid order status."
```

All of these are enforced **server-side** first; any client-side hints (disabled buttons, `min` attributes on number inputs, hiding the cancel button on non-Pending orders) are convenience only.

---

# 5. Testing Design (summary — full evidence in Deliverable 2 and Deliverable 3)

- 65 tests from Stage 2 cover authentication, menu, cart, orders, authorization, admin, and validation (all 33 numbered requirements from the assessment brief).
- 9 additional tests from Stage 3 cover the new cancellation feature end-to-end and at the service-function level.
- Final verified state: **74 tests passed**, 25 non-blocking `DeprecationWarning`s (all from a pre-existing `datetime.datetime.utcnow()` default in `models.py`, tracked as technical debt).
- The suite runs against an isolated, throwaway SQLite database created before the `app` module is imported — the real `canteen.db` is verified byte-for-byte unchanged (MD5) before and after every run in both deliverables.

---

# 6. Known Technical Debt

`Order.created_at` defaults via `datetime.datetime.utcnow()`, which SQLAlchemy flags as deprecated in favour of a timezone-aware `datetime.datetime.now(datetime.UTC)`. This does not currently affect correctness (all comparisons in `cancel_order()` are naive-vs-naive and consistent), but should be migrated before further datetime-sensitive features are added, since mixing naive and aware datetimes raises `TypeError` in Python.
