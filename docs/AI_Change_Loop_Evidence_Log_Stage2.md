# Tactive Assessment — AI Change-Loop Evidence Log

## Project
**Smart Campus Canteen Order & Inventory Management System**

## Deliverable
**AI change-loop evidence log — prompts, changes, failures, corrections, attempts**

---

## 1. Starting Point

### Prompt / Requirement
Stage 2 of the Tactive assessment: given the already-implemented Smart Campus Canteen application (Flask, SQLite, SQLAlchemy, Jinja, HTML/CSS, vanilla JS, Werkzeug password hashing), create a complete pytest automated test suite covering authentication, menu, cart, orders, authorization, admin, and validation — without rebuilding, redesigning, or modifying application behaviour beyond what a genuine bug required.

### Change / Attempt
The existing codebase was inspected first: `app.py`, `models.py`, `services/order_service.py`, `config.py`, and every template, to understand real route behaviour, form field names, and business rules before writing a single test.

### Result
A full understanding of the request/response flow was established, including the fact that `config.py` reads `DATABASE_URL` from the environment at *import time* — a detail that shaped the test-isolation strategy below.

---

## 2. Test Database Isolation Design

### Problem
Naively pointing Flask-SQLAlchemy at a different database mid-test-run is unreliable, because the engine is cached against the already-imported `app` object. Any solution that imports `app` first and reconfigures afterwards risks touching the real `canteen.db`.

### Correction
`tests/conftest.py` sets `DATABASE_URL` to a throwaway temp-file SQLite path **before** importing `app` (and therefore before `config.py` executes), guaranteeing every test session runs against an isolated database that is created fresh per test function (`db.create_all()`/`drop_all()`) and deleted at session end.

### Verification
`canteen.db` was MD5-checksummed before and after every test run in this project. It has remained byte-for-byte identical throughout — confirmed again during this deliverable.

---

## 3. Building the Suite

### Attempt
65 tests were written across `tests/test_auth.py`, `tests/test_authorization.py`, `tests/test_menu.py`, `tests/test_cart.py`, `tests/test_orders.py`, and `tests/test_admin.py`, covering all 33 numbered requirements from the assessment brief (authentication, menu, cart, orders, authorization, admin, validation).

### First Run
```text
pytest -v
```

### Failure
```text
FAILED tests/test_cart.py::test_adding_item_beyond_stock_is_capped
AssertionError: assert (b'Only 2 unit(s) available.' in b'...') or ...
1 failed, 64 passed, 24 warnings
```

### Investigation
The test asserted a flash message on a subsequent `GET /cart` call, but Flask flash messages are consumed (removed from the session) the first time they are rendered — by the redirect response of the request that triggered the cap, not a later page load.

### Correction
The test was rewritten to assert on the response returned by the specific `POST /cart/add/<id>` call that pushed the running quantity past stock, rather than a later unrelated `GET`. **This was a test-authoring bug, not an application bug** — the app's stock-cap behaviour was already correct.

### Result
```text
pytest -v
1 failed, 64 passed
```
(a second, unrelated failure surfaced next — see Section 4)

---

## 4. Second Test Bug

### Failure
```text
FAILED tests/test_orders.py::test_order_uses_current_database_price_not_a_stale_client_value
UnboundLocalError: cannot access local variable 'db' where it is not associated with a value
```

### Investigation
A redundant `from models import db` statement inside the test function body shadowed the already-imported module-level `db`, causing Python to treat `db` as a local variable that was referenced before assignment.

### Correction
The redundant local import was removed; the module-level `db` import was used directly. Again, **this was a test bug, not an application bug**.

### Result
```text
pytest -v
65 passed, 13 warnings
```

---

## 5. Initial Full Test Suite (Baseline)

### Attempt
```text
pytest -v
```

### Result
```text
65 passed, 13 warnings in 11.08s
```

The warnings are non-blocking `DeprecationWarning`s from SQLAlchemy about `datetime.datetime.utcnow()` inside `models.py` (`Order.created_at` default) — pre-existing in the application code, not introduced by the tests.

Full captured log: `logs/initial_full_suite.txt`.

---

## 6. Deliberate Red Run

### Purpose
The Tactive assignment requires evidence of a deliberate failed test run demonstrating the failure → investigation → correction → retest → pass loop against a real application defect (not a test bug).

### Intentional Change
In `app.py`, the admin "add menu item" price validation was temporarily weakened from:

```python
if not name or price <= 0 or stock < 0:
```

to an intentionally incorrect boundary condition:

```python
if not name or price < 0 or stock < 0:
```

This mirrors an off-by-one class of bug: it would let an admin add a menu item priced at exactly `0.00`, which the business rule (and the existing form's `min="0.01"` constraint) says should never be accepted.

### Test
```text
pytest -v
```

### Deliberate Failure
```text
FAILED tests/test_admin.py::test_admin_add_item_with_zero_price_is_rejected
AssertionError: assert b'Enter valid item details.' in b'...<div class="flash success">Menu item added.</div>...'
1 failed, 64 passed, 13 warnings in 11.00s
```

The test correctly caught that a `price=0` item was silently accepted and added to the menu instead of being rejected.

Full captured log: `logs/deliberate_red_run.txt`.

### Correction
The condition was restored to:

```python
if not name or price <= 0 or stock < 0:
```

### Result
```text
pytest -v
65 passed, 13 warnings in 11.07s
```

Full captured log: `logs/final_green_run.txt`.

---

## 7. Database Integrity Check

### Verification
```text
md5sum canteen.db
d130833d302a04042309cec3a76e9a29  canteen.db
```
Identical before and after the entire test-development and deliberate-red-run process. The real production database was never written to at any point.

---

## 8. Non-Blocking Warnings

The final test output contains 13 `DeprecationWarning`s, all pointing to the same root cause:

```python
datetime.datetime.utcnow()
```

used as the default for `Order.created_at` in `models.py`. This does not cause any test failure and is recorded as technical debt rather than a defect, consistent with how the same class of warning was treated in the reference project format.

### Future Correction
```python
datetime.datetime.now(datetime.UTC)
```

No change was made to this line, since fixing it was outside the scope of the testing deliverable and does not affect current behaviour or test outcomes.

---

## 9. Overall AI Change Loop

```text
Requirement
    ↓
Inspect existing application (routes, models, service layer, templates)
    ↓
Design isolated test-database strategy
    ↓
Implement 65 tests across 6 files
    ↓
Run / Test
    ↓
Failure (test bug #1 — flash-message timing)
    ↓
Investigate → Correction → Retest
    ↓
Failure (test bug #2 — shadowed import)
    ↓
Investigate → Correction → Retest
    ↓
Pass (65/65)
    ↓
Deliberate red run (intentional app defect: price boundary)
    ↓
Investigate → Correction → Retest
    ↓
Pass (65/65) — final verified state
```

### Key Evidence

| Stage | Evidence |
|---|---|
| Initial full suite | 65 tests, 65 passed |
| Test bug #1 | Flash-message assertion failure, fixed in test code |
| Test bug #2 | `UnboundLocalError` from shadowed import, fixed in test code |
| Deliberate red run | `1 failed, 64 passed` — `assert b'Enter valid item details.' in b'...Menu item added...'` |
| Correction | Price boundary restored to `price <= 0` |
| Final testing | 65 passed, 13 warnings |
| Database integrity | `canteen.db` MD5 unchanged throughout |

---

## 10. Conclusion

The Smart Campus Canteen test suite was not written and passed on the first attempt. It went through two genuine test-authoring failures (both diagnosed as test bugs, not application bugs, and fixed without touching application logic), followed by a deliberate, intentionally introduced application defect used to demonstrate the red→green change loop, followed by its correction and final verification.

**Final verified state: 65 tests passed, 13 non-blocking deprecation warnings, real database untouched throughout.**

This evidence demonstrates the AI-assisted change loop required for the Tactive assignment.
