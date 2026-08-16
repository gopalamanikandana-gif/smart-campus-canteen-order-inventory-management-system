"""
ADMIN tests.

Covers:
  24. Admin can add a menu item
  25. Admin can edit a menu item
  26. Admin can update price
  27. Admin can update stock
  28. Admin can remove/deactivate a menu item
  29. Admin can update order status

Also covers VALIDATION:
  30. Invalid price is rejected
  31. Invalid stock is rejected
  33. Invalid order status is rejected
"""
from models import MenuItem, Order, db


# 24. Admin can add a menu item ------------------------------------------------

def test_admin_can_add_menu_item(admin_client, app):
    response = admin_client.post(
        "/admin/items/add",
        data={
            "name": "Chole Bhature",
            "category": "Lunch",
            "description": "Spiced chickpeas with fried bread.",
            "price": "90.00",
            "stock": "20",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Menu item added." in response.data

    with app.app_context():
        item = MenuItem.query.filter_by(name="Chole Bhature").first()
        assert item is not None
        assert item.price == 90.00
        assert item.stock == 20
        assert item.is_available is True


# 25. Admin can edit a menu item -----------------------------------------------

def test_admin_can_edit_menu_item(admin_client, menu_item, app):
    response = admin_client.post(
        f"/admin/items/{menu_item['id']}/edit",
        data={
            "name": "Masala Dosa Deluxe",
            "category": "Breakfast",
            "description": "Now with extra chutney.",
            "price": "60.00",
            "stock": "12",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Menu item updated." in response.data

    with app.app_context():
        item = db.session.get(MenuItem, menu_item["id"])
        assert item.name == "Masala Dosa Deluxe"
        assert item.description == "Now with extra chutney."


def test_admin_edit_nonexistent_item_is_handled(admin_client):
    response = admin_client.post(
        "/admin/items/999999/edit",
        data={"name": "X", "category": "Y", "price": "10", "stock": "1"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Menu item not found." in response.data


# 26. Admin can update price -------------------------------------------------

def test_admin_can_update_price(admin_client, menu_item, app):
    admin_client.post(
        f"/admin/items/{menu_item['id']}/edit",
        data={"name": menu_item["name"], "category": "Breakfast", "price": "77.50", "stock": str(menu_item["stock"])},
        follow_redirects=True,
    )
    with app.app_context():
        item = db.session.get(MenuItem, menu_item["id"])
        assert item.price == 77.50


# 27. Admin can update stock -------------------------------------------------

def test_admin_can_update_stock(admin_client, menu_item, app):
    admin_client.post(
        f"/admin/items/{menu_item['id']}/edit",
        data={"name": menu_item["name"], "category": "Breakfast", "price": str(menu_item["price"]), "stock": "99"},
        follow_redirects=True,
    )
    with app.app_context():
        item = db.session.get(MenuItem, menu_item["id"])
        assert item.stock == 99


def test_admin_setting_stock_to_zero_marks_item_unavailable(admin_client, menu_item, app):
    admin_client.post(
        f"/admin/items/{menu_item['id']}/edit",
        data={"name": menu_item["name"], "category": "Breakfast", "price": str(menu_item["price"]), "stock": "0"},
        follow_redirects=True,
    )
    with app.app_context():
        item = db.session.get(MenuItem, menu_item["id"])
        assert item.stock == 0
        assert item.is_available is False


# 28. Admin can remove/deactivate a menu item -----------------------------------

def test_admin_can_remove_menu_item(admin_client, menu_item, app):
    response = admin_client.post(f"/admin/items/{menu_item['id']}/delete", follow_redirects=True)
    assert response.status_code == 200
    assert b"Menu item removed from the active menu." in response.data

    with app.app_context():
        item = db.session.get(MenuItem, menu_item["id"])
        # Soft-delete: row still exists but is deactivated and zeroed out.
        assert item is not None
        assert item.is_available is False
        assert item.stock == 0

    # Removed item must disappear from the public menu.
    menu_page = admin_client.get("/menu")
    assert menu_item["name"].encode() not in menu_page.data


# 29. Admin can update order status --------------------------------------------

def test_admin_can_update_order_status(admin_client, student_user, menu_item, app):
    # Create an order directly (order creation itself is covered in test_orders.py).
    with app.app_context():
        from models import db, OrderItem
        order = Order(user_id=student_user["id"], status="Pending", total=menu_item["price"])
        order.items.append(OrderItem(
            menu_item_id=menu_item["id"], item_name=menu_item["name"],
            unit_price=menu_item["price"], quantity=1, subtotal=menu_item["price"],
        ))
        db.session.add(order)
        db.session.commit()
        order_id = order.id

    response = admin_client.post(
        f"/admin/orders/{order_id}/status",
        data={"status": "Preparing"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"status updated." in response.data

    with app.app_context():
        assert db.session.get(Order, order_id).status == "Preparing"


# 30. Invalid price is rejected --------------------------------------------------

def test_admin_add_item_with_zero_price_is_rejected(admin_client, app):
    response = admin_client.post(
        "/admin/items/add",
        data={"name": "Bad Price Item", "category": "Snacks", "price": "0", "stock": "5"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Enter valid item details." in response.data
    with app.app_context():
        assert MenuItem.query.filter_by(name="Bad Price Item").first() is None


def test_admin_add_item_with_negative_price_is_rejected(admin_client, app):
    response = admin_client.post(
        "/admin/items/add",
        data={"name": "Negative Price Item", "category": "Snacks", "price": "-5", "stock": "5"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Enter valid item details." in response.data
    with app.app_context():
        assert MenuItem.query.filter_by(name="Negative Price Item").first() is None


def test_admin_add_item_with_non_numeric_price_is_rejected(admin_client, app):
    response = admin_client.post(
        "/admin/items/add",
        data={"name": "NaN Price Item", "category": "Snacks", "price": "abc", "stock": "5"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Price and stock must be valid numbers." in response.data
    with app.app_context():
        assert MenuItem.query.filter_by(name="NaN Price Item").first() is None


# 31. Invalid stock is rejected ------------------------------------------------

def test_admin_add_item_with_negative_stock_is_rejected(admin_client, app):
    response = admin_client.post(
        "/admin/items/add",
        data={"name": "Negative Stock Item", "category": "Snacks", "price": "10", "stock": "-1"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Enter valid item details." in response.data
    with app.app_context():
        assert MenuItem.query.filter_by(name="Negative Stock Item").first() is None


def test_admin_add_item_with_non_numeric_stock_is_rejected(admin_client, app):
    response = admin_client.post(
        "/admin/items/add",
        data={"name": "NaN Stock Item", "category": "Snacks", "price": "10", "stock": "xyz"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Price and stock must be valid numbers." in response.data
    with app.app_context():
        assert MenuItem.query.filter_by(name="NaN Stock Item").first() is None


# 33. Invalid order status is rejected ------------------------------------------

def test_admin_invalid_order_status_is_rejected(admin_client, student_user, menu_item, app):
    with app.app_context():
        from models import db, OrderItem
        order = Order(user_id=student_user["id"], status="Pending", total=menu_item["price"])
        order.items.append(OrderItem(
            menu_item_id=menu_item["id"], item_name=menu_item["name"],
            unit_price=menu_item["price"], quantity=1, subtotal=menu_item["price"],
        ))
        db.session.add(order)
        db.session.commit()
        order_id = order.id

    response = admin_client.post(
        f"/admin/orders/{order_id}/status",
        data={"status": "TotallyMadeUpStatus"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Invalid order status." in response.data

    with app.app_context():
        assert db.session.get(Order, order_id).status == "Pending"  # unchanged


def test_admin_update_status_for_nonexistent_order_is_rejected(admin_client):
    response = admin_client.post(
        "/admin/orders/999999/status",
        data={"status": "Completed"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Invalid order status." in response.data
