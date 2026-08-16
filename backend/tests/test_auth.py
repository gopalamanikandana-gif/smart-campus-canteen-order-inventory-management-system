def test_register_and_login(client):
    response = client.post(
        "/auth/register",
        json={
            "name": "Test Student",
            "email": "test@example.com",
            "password": "Password@123",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["user"]["role"] == "STUDENT"
    assert data["access_token"]

    login = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "Password@123"},
    )
    assert login.status_code == 200


def test_duplicate_registration_rejected(client):
    payload = {
        "name": "Test Student",
        "email": "test@example.com",
        "password": "Password@123",
    }
    assert client.post("/auth/register", json=payload).status_code == 201
    assert client.post("/auth/register", json=payload).status_code == 409
