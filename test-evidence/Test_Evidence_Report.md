# Tactive Assessment — Test Evidence Report

## Smart Campus Canteen Order & Inventory Management System

Deliverable 2: Test suite plus captured run output, including one deliberate red run.

| Evidence | Result | Status |
|---|---|---|
| Initial full suite (after test-bug fixes) | 65 passed, 13 warnings | Passed |
| Deliberate red run | 1 failed, 64 passed, 13 warnings | Expected failure |
| Recovery run | 65 passed, 13 warnings | Passed |
| Final full suite | 65 passed, 13 warnings | Passed |
| Real database (`canteen.db`) integrity | MD5 identical before/after | Untouched |

---

## 1. Test Coverage

The captured pytest suite validates all 33 numbered requirements from the assessment brief:

- **Authentication** — valid registration, invalid registration data, duplicate email, valid login, invalid login, logout
- **Menu** — item viewing, search (including case-insensitivity), unavailable/out-of-stock items rejected at the server
- **Cart** — add to cart, quantity update, item removal, empty-cart handling, stock-limit capping
- **Orders** — valid placement, total calculation, stock deduction, insufficient-stock rejection, order history, server-side (never client-supplied) pricing
- **Authorization** — unauthenticated access blocked, student blocked from admin routes, admin access confirmed
- **Admin** — add/edit menu item, price update, stock update, item removal/deactivation, order-status update
- **Validation** — invalid price rejected, invalid stock rejected, invalid quantity rejected, invalid order status rejected

65 test functions across 6 files: `test_auth.py`, `test_authorization.py`, `test_menu.py`, `test_cart.py`, `test_orders.py`, `test_admin.py`.

---

## 2. Test-Isolation Evidence

Since `config.py` reads `DATABASE_URL` at import time, `tests/conftest.py` sets this environment variable to a throwaway temp-file SQLite database **before** `app` is imported, and creates/drops the schema per test. This was verified by MD5-checksumming `canteen.db` before and after every run in this deliverable:

```text
d130833d302a04042309cec3a76e9a29  canteen.db   (before all testing work)
d130833d302a04042309cec3a76e9a29  canteen.db   (after deliberate red run + recovery)
```

No difference — the production database was never written to.

---

## 3. Deliberate Red Run

To demonstrate a controlled failure-and-correction loop against a real application defect, the admin "add menu item" price check was intentionally weakened from:

```python
if not name or price <= 0 or stock < 0:
```

to an off-by-one boundary bug:

```python
if not name or price < 0 or stock < 0:
```

This would let an admin add a menu item priced at exactly `0.00`. The existing test `test_admin_add_item_with_zero_price_is_rejected` caught it immediately:

```text
FAILED tests/test_admin.py::test_admin_add_item_with_zero_price_is_rejected
AssertionError: assert b'Enter valid item details.' in b'...<div class="flash success">Menu item added.</div>...'
1 failed, 64 passed, 13 warnings in 11.00s
```

Full captured terminal log: `logs/deliberate_red_run.txt`.

---

## 4. Correction and Recovery

The condition was restored to `price <= 0`. The suite was re-run immediately:

```text
65 passed, 13 warnings in 11.07s
```

Full captured terminal log: `logs/final_green_run.txt`.

---

## 5. Test-Authoring Bugs Found During Development (for transparency)

Two failures were also encountered and resolved *while writing the test suite itself*, before the deliberate red run above. Both were diagnosed as bugs in the tests, not the application, and were fixed without touching application code:

1. **Flash-message timing** — `test_adding_item_beyond_stock_is_capped` checked a flash message on a later `GET /cart`, after Flask had already consumed it. Fixed by asserting on the response of the request that actually triggered the cap.
2. **Shadowed import** — `test_order_uses_current_database_price_not_a_stale_client_value` had a redundant local `from models import db` that shadowed the module-level import, causing `UnboundLocalError`. Fixed by removing the redundant import.

---

## 6. Final Green Run

```text
pytest -v
...
65 passed, 13 warnings in 11.07s
```

Full captured terminal log: `logs/final_green_run.txt`.

---

## 7. Warnings

The suite reports 13 non-blocking `DeprecationWarning`s, all from the same source:

```python
datetime.datetime.utcnow()
```

used as the SQLAlchemy default for `Order.created_at` in the existing `models.py`. This is pre-existing application code, does not cause any test failure, and is recorded as technical debt. Recommended future migration: `datetime.datetime.now(datetime.UTC)`.

---

## 8. Evidence Files

```text
evidence/
├── AI_Change_Loop_Evidence_Log.md
├── Test_Evidence_Report.md
└── logs/
    ├── initial_full_suite.txt      (65 passed, baseline)
    ├── deliberate_red_run.txt      (1 failed, 64 passed — intentional)
    └── final_green_run.txt         (65 passed, final verified state)
```

No screenshots were captured, since this run was executed in a headless CLI environment rather than an IDE with a visible terminal pane; the raw `pytest -v` terminal logs above serve as the equivalent evidence.

**Final state: 65 tests passed, 13 non-blocking deprecation warnings, real database untouched throughout.**
