from app.database import SessionLocal
from app.models import MenuItem, User


def register(client, email="student@example.com"):
    r = client.post(
        "/auth/register",
        json={"name": "Student", "email": email, "password": "Password@123"},
    )
    return r.json()["access_token"]


def add_menu(client, admin_token=None, price=100, stock=10):
    # Tests create an admin directly through the database to avoid testing admin
    # setup repeatedly in every case.
    db = SessionLocal()
    from app.auth import hash_password
    admin = User(
        name="Admin",
        email="admin@example.com",
        password_hash=hash_password("Admin@123"),
        role="ADMIN",
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    db.close()

    login = client.post(
        "/auth/login",
        json={"email": "admin@example.com", "password": "Admin@123"},
    )
    token = login.json()["access_token"]

    r = client.post(
        "/menu",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Burger",
            "description": "Test burger",
            "price": price,
            "stock": stock,
            "is_available": True,
        },
    )
    return r.json()["id"], token


def test_valid_order_reduces_stock_and_uses_db_price(client):
    token = register(client)
    item_id, _ = add_menu(client, price=80, stock=10)

    response = client.post(
        "/orders",
        headers={"Authorization": f"Bearer {token}"},
        json={"items": [{"menu_item_id": item_id, "quantity": 2}]},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["total_amount"] == 160
    assert data["items"][0]["unit_price"] == 80
    assert data["items"][0]["subtotal"] == 160

    menu = client.get("/menu").json()
    assert menu[0]["stock"] == 8


def test_insufficient_stock_rejected(client):
    token = register(client)
    item_id, _ = add_menu(client, price=50, stock=2)

    response = client.post(
        "/orders",
        headers={"Authorization": f"Bearer {token}"},
        json={"items": [{"menu_item_id": item_id, "quantity": 3}]},
    )

    assert response.status_code == 400
    assert "Insufficient stock" in response.json()["detail"]


def test_max_quantity_rejected(client):
    token = register(client)
    item_id, _ = add_menu(client, price=50, stock=20)

    response = client.post(
        "/orders",
        headers={"Authorization": f"Bearer {token}"},
        json={"items": [{"menu_item_id": item_id, "quantity": 6}]},
    )

    assert response.status_code == 400


def test_empty_cart_rejected(client):
    token = register(client)

    response = client.post(
        "/orders",
        headers={"Authorization": f"Bearer {token}"},
        json={"items": []},
    )

    assert response.status_code == 422


def test_unauthenticated_order_rejected(client):
    response = client.post(
        "/orders",
        json={"items": [{"menu_item_id": 1, "quantity": 1}]},
    )
    assert response.status_code == 403


def test_student_cannot_create_menu(client):
    token = register(client)

    response = client.post(
        "/menu",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Secret",
            "description": "",
            "price": 10,
            "stock": 10,
            "is_available": True,
        },
    )
    assert response.status_code == 403
