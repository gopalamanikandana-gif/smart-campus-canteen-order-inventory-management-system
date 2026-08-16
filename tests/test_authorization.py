"""
AUTHORIZATION tests.

Covers:
  21. Unauthenticated users cannot access protected functionality
  22. Student cannot access admin dashboard
  23. Admin can access admin dashboard
"""
from tests.conftest import login


# 21. Unauthenticated users cannot access protected functionality -------------

def test_unauthenticated_user_cannot_view_cart(client, app):
    response = client.get("/cart", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_unauthenticated_user_cannot_view_order_history(client, app):
    response = client.get("/orders", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_unauthenticated_user_cannot_add_to_cart(client, menu_item):
    response = client.post(f"/cart/add/{menu_item['id']}", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_unauthenticated_user_cannot_place_order(client, app):
    response = client.post("/orders/place", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_unauthenticated_user_cannot_access_admin_dashboard(client, app):
    response = client.get("/admin", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


# 22. Student cannot access admin dashboard / admin actions -------------------

def test_student_cannot_access_admin_dashboard(student_client):
    response = student_client.get("/admin", follow_redirects=True)
    assert response.status_code == 200
    assert b"Admin access required." in response.data
    # Should be redirected to the student menu, not shown the dashboard.
    assert b"ADMIN CONTROL CENTER" not in response.data


def test_student_cannot_add_menu_item(student_client):
    response = student_client.post(
        "/admin/items/add",
        data={"name": "Hacked Item", "category": "Snacks", "price": "10", "stock": "5"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Admin access required." in response.data


def test_student_cannot_update_order_status(student_client, admin_user, menu_item, app):
    # An admin-only endpoint must reject a student even if an order id exists.
    response = student_client.post(
        "/admin/orders/1/status",
        data={"status": "Completed"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Admin access required." in response.data


# 23. Admin can access admin dashboard -----------------------------------------

def test_admin_can_access_admin_dashboard(admin_client):
    response = admin_client.get("/admin")
    assert response.status_code == 200
    assert b"ADMIN CONTROL CENTER" in response.data


def test_admin_login_redirects_directly_to_dashboard(client, admin_user):
    response = login(client, admin_user["email"], admin_user["password"])
    assert response.status_code == 200
    assert b"ADMIN CONTROL CENTER" in response.data
