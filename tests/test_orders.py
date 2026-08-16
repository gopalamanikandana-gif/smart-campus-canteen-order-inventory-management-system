"""
ORDER tests.

Covers:
  15. Valid order can be placed
  16. Order total is calculated correctly
  17. Stock decreases after successful order
  18. Insufficient stock prevents the order
  19. Order appears in student's order history
  20. Backend/database price is used rather than trusting client input

Also covers part of VALIDATION:
  32. Invalid quantity is rejected (at the order-creation layer)
"""
import pytest

from models import MenuItem, Order, db
from services.order_service import create_order_from_cart


# 15. Valid order can be placed --------------------------------------------------

def test_valid_order_can_be_placed(student_client, menu_item, app):
    student_client.post(f"/cart/add/{menu_item['id']}", follow_redirects=True)
    response = student_client.post("/orders/place", follow_redirects=True)

    assert response.status_code == 200
    assert b"placed successfully" in response.data

    with app.app_context():
        orders = Order.query.all()
        assert len(orders) == 1
        assert orders[0].status == "Pending"
        assert len(orders[0].items) == 1
        assert orders[0].items[0].item_name == menu_item["name"]


# 16. Order total is calculated correctly ----------------------------------------

def test_order_total_is_calculated_correctly(student_client, menu_item, app):
    student_client.post(f"/cart/add/{menu_item['id']}", follow_redirects=True)  # qty 1
    student_client.post(f"/cart/add/{menu_item['id']}", follow_redirects=True)  # qty 2
    student_client.post(f"/cart/add/{menu_item['id']}", follow_redirects=True)  # qty 3
    student_client.post("/orders/place", follow_redirects=True)

    with app.app_context():
        order = Order.query.first()
        expected_total = round(menu_item["price"] * 3, 2)
        assert order.total == expected_total
        assert order.items[0].subtotal == expected_total


def test_order_total_sums_multiple_distinct_items(student_client, app):
    from tests.conftest import create_menu_item

    with app.app_context():
        item_a = create_menu_item(name="Item A", price=25.0, stock=10)
        item_b = create_menu_item(name="Item B", price=40.0, stock=10)

    student_client.post(f"/cart/add/{item_a}", follow_redirects=True)
    student_client.post(f"/cart/add/{item_b}", follow_redirects=True)
    student_client.post("/orders/place", follow_redirects=True)

    with app.app_context():
        order = Order.query.first()
        assert order.total == round(25.0 + 40.0, 2)


# 17. Stock decreases after successful order --------------------------------------

def test_stock_decreases_after_successful_order(student_client, menu_item, app):
    student_client.post(f"/cart/add/{menu_item['id']}", follow_redirects=True)
    student_client.post(f"/cart/add/{menu_item['id']}", follow_redirects=True)  # qty 2
    student_client.post("/orders/place", follow_redirects=True)

    with app.app_context():
        item = db.session.get(MenuItem, menu_item["id"])
        assert item.stock == menu_item["stock"] - 2


def test_item_marked_unavailable_when_stock_reaches_zero(student_client, low_stock_item, app):
    # low_stock_item has stock=2; buy exactly all of it.
    for _ in range(2):
        student_client.post(f"/cart/add/{low_stock_item['id']}", follow_redirects=True)
    student_client.post("/orders/place", follow_redirects=True)

    with app.app_context():
        item = db.session.get(MenuItem, low_stock_item["id"])
        assert item.stock == 0
        assert item.is_available is False


# 18. Insufficient stock prevents the order ---------------------------------------

def test_insufficient_stock_prevents_order(student_client, low_stock_item, app):
    # Bypass the UI cap by writing a cart quantity greater than stock
    # directly into the session, simulating a tampered/forged request.
    with student_client.session_transaction() as sess:
        sess["cart"] = {str(low_stock_item["id"]): low_stock_item["stock"] + 10}

    response = student_client.post("/orders/place", follow_redirects=True)
    assert response.status_code == 200
    assert b"Not enough stock" in response.data

    with app.app_context():
        assert Order.query.count() == 0
        item = db.session.get(MenuItem, low_stock_item["id"])
        assert item.stock == low_stock_item["stock"]  # unchanged


def test_order_service_rejects_insufficient_stock_directly(app, low_stock_item, student_user):
    """Unit-level check of the order service itself (not just the route)."""
    with app.app_context():
        with pytest.raises(ValueError, match="Not enough stock"):
            create_order_from_cart(student_user["id"], {str(low_stock_item["id"]): low_stock_item["stock"] + 1})


# 19. Order appears in student's order history --------------------------------

def test_order_appears_in_history(student_client, menu_item):
    student_client.post(f"/cart/add/{menu_item['id']}", follow_redirects=True)
    place_response = student_client.post("/orders/place", follow_redirects=True)
    assert b"placed successfully" in place_response.data

    history = student_client.get("/orders")
    assert history.status_code == 200
    assert menu_item["name"].encode() in history.data


def test_order_history_only_shows_own_orders(client, student_user, second_student_user, menu_item, app):
    from tests.conftest import login

    login(client, student_user["email"], student_user["password"])
    client.post(f"/cart/add/{menu_item['id']}", follow_redirects=True)
    client.post("/orders/place", follow_redirects=True)
    client.get("/logout", follow_redirects=True)

    login(client, second_student_user["email"], second_student_user["password"])
    history = client.get("/orders")
    assert menu_item["name"].encode() not in history.data


# 20. Backend/database price is used rather than trusting client input -------------

def test_order_uses_current_database_price_not_a_stale_client_value(student_client, menu_item, app):
    # Add to cart while price is 50.0.
    student_client.post(f"/cart/add/{menu_item['id']}", follow_redirects=True)

    # Simulate the price changing on the server (e.g. an admin update) AFTER
    # the item was added to the cart but BEFORE the order is placed.
    with app.app_context():
        item = db.session.get(MenuItem, menu_item["id"])
        item.price = 999.99
        db.session.commit()

    student_client.post("/orders/place", follow_redirects=True)

    with app.app_context():
        order = Order.query.first()
        # The order must reflect the current DB price (999.99), never the
        # price that was in effect when the item was merely added to cart.
        assert order.items[0].unit_price == 999.99
        assert order.total == 999.99


def test_order_ignores_extraneous_client_supplied_fields(student_client, menu_item, app):
    # The cart/order flow never reads price/total from the request body at
    # all — only from server-side session + DB. Prove tampered form fields
    # sent alongside the request have zero effect on the computed total.
    student_client.post(f"/cart/add/{menu_item['id']}", follow_redirects=True)

    response = student_client.post(
        "/orders/place",
        data={"price": "0.01", "total": "0.01", "unit_price": "0.01"},
        follow_redirects=True,
    )
    assert response.status_code == 200

    with app.app_context():
        order = Order.query.first()
        assert order.total == menu_item["price"]  # unaffected by the bogus fields

