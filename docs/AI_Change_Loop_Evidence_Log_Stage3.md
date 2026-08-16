# Tactive Assessment — Stage 3: AI Change-Loop Evidence Log

## Project
**Smart Campus Canteen Order & Inventory Management System**

## Feature Request Given to the AI
> "Add student order cancellation: a student should be able to cancel their own order,
> but only while it is still `Pending` and only within 5 minutes of placing it. Cancelling
> must restore the stock that was deducted, and it must not be possible to cancel an
> order that belongs to someone else. Implement the change, then run the existing test
> suite against it, fix whatever breaks, and add tests for the new behaviour."

This is the literal prompt used to drive the Stage 3 loop below.

---

## 1. Implementation Attempt

### Change made by the AI
1. `services/order_service.py` — added `cancel_order(order_id, user_id, now=None)`:
   - Validates the order exists **and** belongs to the requesting user (`"Order not found."` otherwise — deliberately not leaking whether the order exists for someone else).
   - Validates `order.status == "Pending"` (`"This order can no longer be cancelled."` otherwise).
   - Validates the 5-minute window (`CANCELLATION_WINDOW_MINUTES = 5`) against `order.created_at` (`"The cancellation window has expired."` otherwise).
   - On success: restores `MenuItem.stock` for every line item, re-flags `is_available = True` if stock is now positive, and sets `order.status = "Cancelled"`.
   - Accepts an optional `now` parameter so the time-window rule is testable without sleeping or monkeypatching the real clock.
2. `app.py` — added `POST /orders/<int:order_id>/cancel`, `@login_required`, calling the new service function and flashing success/failure.
3. `templates/orders.html` — added a "Cancel order" button, shown only when `order.status == 'Pending'` (the server still enforces the 5-minute window and ownership independently — the button visibility is UX only, not the security boundary).
4. `tests/test_order_cancellation.py` — 9 new tests covering: successful cancellation + stock restoration (single and multi-unit), expired window, non-Pending order, cross-student ownership, nonexistent order, login requirement, and cancel-button visibility.

### First Test Run
```text
pytest -v
```

### Result
```text
FAILED tests/test_order_cancellation.py::test_cancel_non_pending_order_is_rejected
FAILED tests/test_order_cancellation.py::test_cancel_button_hidden_for_non_pending_orders
2 failed, 72 passed, 25 warnings in 15.20s
```

Full captured log: `logs/stage3_attempt1_failures.txt`.

---

## 2. Detect What Broke

### Symptom
`test_cancel_non_pending_order_is_rejected` expected the cancellation to be rejected with `"can no longer be cancelled"` after an admin moved the order to `Preparing`. Instead, the order showed status **`Cancelled`** in the response — the cancellation had gone through when it should have been blocked.

### Investigation
Both failing tests used **both** `student_client` and `admin_client` as fixtures in the same test. Tracing through `tests/conftest.py`:

```python
@pytest.fixture()
def student_client(client, student_user):
    login(client, student_user["email"], student_user["password"])
    return client

@pytest.fixture()
def admin_client(client, admin_user):
    login(client, admin_user["email"], admin_user["password"])
    return client
```

Both fixtures depend on the same `client` fixture. Pytest resolves and caches a fixture once per test node, so `student_client` and `admin_client` were actually **the same Flask test client object — one shared cookie jar, one shared session**. When the `admin_client` fixture ran its `login()` call during test setup, it silently logged the "student" session out and replaced it with the admin session, because they were never two independent clients to begin with.

This bug only surfaces once a test uses *both* a student action and an admin action together, which is exactly what the new cancellation tests needed (student places an order → admin changes its status → student tries to cancel) but none of the Stage 2 tests happened to do.

### Root cause classification
**Test-fixture design bug in `conftest.py`**, not an application bug. `app.py` and `services/order_service.py` behaved correctly throughout — the fixtures were misrepresenting two different logged-in users as one.

---

## 3. Correction

`conftest.py` was changed so each fixture gets its own independent `app.test_client()` instead of sharing the module-level `client` fixture:

```python
@pytest.fixture()
def student_client(app, student_user):
    c = app.test_client()
    login(c, student_user["email"], student_user["password"])
    return c

@pytest.fixture()
def admin_client(app, admin_user):
    c = app.test_client()
    login(c, admin_user["email"], admin_user["password"])
    return c
```

No application code (`app.py`, `services/order_service.py`, `templates/`) required any change — the feature implementation was correct on the first attempt.

---

## 4. Retest

### Second Test Run
```text
pytest -v
```

### Result
```text
74 passed, 25 warnings in 15.25s
```

Full captured log: `logs/stage3_attempt2_final_green.txt`.

All 65 pre-existing tests from Stage 2 still pass — the fixture fix caused no regressions — and all 9 new cancellation tests pass.

---

## 5. Attempts Summary

| Attempt | Action | Result |
|---|---|---|
| 1 | Implement feature + write 9 new tests, run full suite | `2 failed, 72 passed` |
| 2 | Diagnose shared-client fixture bug, fix `conftest.py` only | `74 passed` (final) |

**Two attempts.** No manual code review was needed beyond reading the failing assertion's rendered HTML output, which directly showed the order had been cancelled when it shouldn't have been — that was the thread that led to the fixture investigation.

---

## 6. Database Integrity Check

```text
md5sum canteen.db
d130833d302a04042309cec3a76e9a29  canteen.db   (unchanged throughout Stage 3)
```

---

## 7. Where the Loop Did *Not* Fail

Everything above was closed by the AI loop itself — implement, run, detect, fix, retest, pass — with **no manual code changes required outside of what the loop itself produced**. The one place a human (the person directing the AI) had to make a judgement call was in classifying the failure as a test-fixture bug rather than an application bug, by reading the actual response HTML in the assertion diff rather than trusting the test's own expectation.

---

## 8. Conclusion

The Stage 3 feature — student order cancellation within a 5-minute grace window — was implemented in one pass with correct application logic. The change loop caught a real, non-obvious defect: two fixtures that looked like they represented two different logged-in users but actually shared one session. This is exactly the kind of bug that a "test suite that always passes" would never catch, and is direct evidence that this test suite can fail and did fail for a real reason before being corrected.

**Final verified state: 74 tests passed (65 Stage 2 + 9 new), 25 non-blocking deprecation warnings, real database untouched throughout.**
