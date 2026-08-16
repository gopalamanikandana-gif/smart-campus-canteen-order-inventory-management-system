"""
Tests for the new FEATURE (Stage 3 — AI change loop):
Student self-cancellation of a Pending order within a 5-minute grace window,
with stock restored to the menu.

Covers:
  - Valid cancellation within the window restores stock and marks the order Cancelled
  - Cancellation after the window has expired is rejected
  - Cancellation of an order that is no longer Pending (e.g. already Preparing) is rejected
  - A student cannot cancel another student's order
  - Cancelling a nonexistent order is rejected
  - Cancel button is not shown for non-Pending orders
"""
from datetime import datetime, timedelta

import pytest

from models import MenuItem, Order, db
from services.order_service import cancel_order


def _place_single_item_order(client, item_id):
    client.post(f"/cart/add/{item_id}", follow_redirects=True)
    return client.post("/orders/place", follow_redirects=True)


def test_student_can_cancel_pending_order_within_window(student_client, menu_item, app):
    _place_single_item_order(student_client, menu_item["id"])

    with app.app_context():
        order = Order.query.first()
        stock_after_order = db.session.get(MenuItem, menu_item["id"]).stock
        assert stock_after_order == menu_item["stock"] - 1

    response = student_client.post(f"/orders/{order.id}/cancel", follow_redirects=True)
    assert response.status_code == 200
    assert b"cancelled" in response.data

    with app.app_context():
        cancelled = db.session.get(Order, order.id)
        assert cancelled.status == "Cancelled"
        item = db.session.get(MenuItem, menu_item["id"])
        assert item.stock == menu_item["stock"]  # fully restored
        assert item.is_available is True


def test_cancel_restores_stock_for_multiple_units(student_client, menu_item, app):
    student_client.post(f"/cart/add/{menu_item['id']}", follow_redirects=True)
    student_client.post(f"/cart/add/{menu_item['id']}", follow_redirects=True)  # qty 2
    student_client.post("/orders/place", follow_redirects=True)

    with app.app_context():
        order = Order.query.first()

    student_client.post(f"/orders/{order.id}/cancel", follow_redirects=True)

    with app.app_context():
        item = db.session.get(MenuItem, menu_item["id"])
        assert item.stock == menu_item["stock"]


def test_cancel_after_window_expired_is_rejected(app, student_user, menu_item):
    """Directly exercises the service layer with a simulated 'now' well past the window."""
    with app.app_context():
        order = Order(user_id=student_user["id"], status="Pending", total=menu_item["price"])
        from models import OrderItem
        order.items.append(OrderItem(
            menu_item_id=menu_item["id"], item_name=menu_item["name"],
            unit_price=menu_item["price"], quantity=1, subtotal=menu_item["price"],
        ))
        db.session.add(order)
        db.session.commit()
        order_id = order.id
        placed_at = order.created_at

        with pytest.raises(ValueError, match="cancellation window has expired"):
            cancel_order(order_id, student_user["id"], now=placed_at + timedelta(minutes=10))

        # Status and stock must be unchanged after the rejected attempt.
        unchanged = db.session.get(Order, order_id)
        assert unchanged.status == "Pending"


def test_cancel_non_pending_order_is_rejected(student_client, admin_client, menu_item, app):
    _place_single_item_order(student_client, menu_item["id"])
    with app.app_context():
        order = Order.query.first()

    # Admin moves it out of Pending before the student tries to cancel.
    admin_client.post(f"/admin/orders/{order.id}/status", data={"status": "Preparing"}, follow_redirects=True)

    response = student_client.post(f"/orders/{order.id}/cancel", follow_redirects=True)
    assert b"can no longer be cancelled" in response.data

    with app.app_context():
        unchanged = db.session.get(Order, order.id)
        assert unchanged.status == "Preparing"
        item = db.session.get(MenuItem, menu_item["id"])
        assert item.stock == menu_item["stock"] - 1  # not restored


def test_student_cannot_cancel_another_students_order(client, student_user, second_student_user, menu_item, app):
    from tests.conftest import login

    login(client, student_user["email"], student_user["password"])
    _place_single_item_order(client, menu_item["id"])
    with app.app_context():
        order = Order.query.first()
    client.get("/logout", follow_redirects=True)

    login(client, second_student_user["email"], second_student_user["password"])
    response = client.post(f"/orders/{order.id}/cancel", follow_redirects=True)
    assert b"Order not found." in response.data

    with app.app_context():
        unchanged = db.session.get(Order, order.id)
        assert unchanged.status == "Pending"  # untouched by the other student


def test_cancel_nonexistent_order_is_rejected(student_client):
    response = student_client.post("/orders/999999/cancel", follow_redirects=True)
    assert response.status_code == 200
    assert b"Order not found." in response.data


def test_cancel_requires_login(client, app):
    response = client.post("/orders/1/cancel", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_cancel_button_hidden_for_non_pending_orders(student_client, admin_client, menu_item, app):
    _place_single_item_order(student_client, menu_item["id"])
    with app.app_context():
        order = Order.query.first()

    admin_client.post(f"/admin/orders/{order.id}/status", data={"status": "Completed"}, follow_redirects=True)

    history = student_client.get("/orders")
    assert b"Cancel order" not in history.data


def test_cancel_button_shown_for_pending_orders(student_client, menu_item):
    _place_single_item_order(student_client, menu_item["id"])
    history = student_client.get("/orders")
    assert b"Cancel order" in history.data
