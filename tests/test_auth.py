"""
AUTHENTICATION tests.

Covers:
  1. Student registration with valid data
  2. Registration with invalid data
  3. Duplicate email registration
  4. Valid student login
  5. Invalid login
  6. Logout
"""
import pytest

from models import User
from tests.conftest import login, logout


# 1. Student registration with valid data ------------------------------------

def test_register_with_valid_data_creates_student(client, app):
    response = client.post(
        "/register",
        data={"name": "Alice Student", "email": "alice@canteen.local", "password": "SecurePass1"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Registration successful" in response.data

    with app.app_context():
        user = User.query.filter_by(email="alice@canteen.local").first()
        assert user is not None
        assert user.name == "Alice Student"
        assert user.role == "student"  # self-registration always creates a student
        # Password must be hashed, never stored in plain text.
        assert user.password_hash != "SecurePass1"


# 2. Registration with invalid data -------------------------------------------

@pytest.mark.parametrize(
    "payload, expected_flash",
    [
        ({"name": "A", "email": "short@canteen.local", "password": "SecurePass1"}, b"Enter a valid name."),
        ({"name": "Valid Name", "email": "not-an-email", "password": "SecurePass1"}, b"Enter a valid email."),
        ({"name": "Valid Name", "email": "novalid@canteen.local", "password": "123"}, b"Password must be at least 6 characters."),
    ],
)
def test_register_with_invalid_data_is_rejected(client, app, payload, expected_flash):
    response = client.post("/register", data=payload, follow_redirects=True)
    assert response.status_code == 200
    assert expected_flash in response.data

    with app.app_context():
        assert User.query.filter_by(email=payload["email"]).first() is None


# 3. Duplicate email registration ----------------------------------------------

def test_duplicate_email_registration_is_rejected(client, app):
    payload = {"name": "First User", "email": "dupe@canteen.local", "password": "SecurePass1"}
    first = client.post("/register", data=payload, follow_redirects=True)
    assert b"Registration successful" in first.data

    second = client.post(
        "/register",
        data={"name": "Second User", "email": "dupe@canteen.local", "password": "AnotherPass1"},
        follow_redirects=True,
    )
    assert b"Email is already registered." in second.data

    with app.app_context():
        matches = User.query.filter_by(email="dupe@canteen.local").all()
        assert len(matches) == 1
        assert matches[0].name == "First User"  # second registration did not overwrite the first


# 4. Valid student login --------------------------------------------------------

def test_valid_student_login_succeeds(client, student_user):
    response = login(client, student_user["email"], student_user["password"])
    assert response.status_code == 200
    # After login, a protected page should be reachable without redirect to /login.
    orders_page = client.get("/orders")
    assert orders_page.status_code == 200
    assert b"Please log in to continue." not in orders_page.data


def test_valid_login_redirects_student_to_menu(client, student_user):
    response = client.post(
        "/login",
        data={"email": student_user["email"], "password": student_user["password"]},
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/menu")


def test_valid_login_redirects_admin_to_dashboard(client, admin_user):
    response = client.post(
        "/login",
        data={"email": admin_user["email"], "password": admin_user["password"]},
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/admin")


# 5. Invalid login ----------------------------------------------------------------

def test_login_with_wrong_password_is_rejected(client, student_user):
    response = login(client, student_user["email"], "WrongPassword1")
    assert response.status_code == 200
    assert b"Invalid email or password." in response.data
    # User must not be authenticated afterwards.
    protected = client.get("/orders", follow_redirects=False)
    assert protected.status_code == 302
    assert "/login" in protected.headers["Location"]


def test_login_with_unknown_email_is_rejected(client, app):
    response = login(client, "nobody@canteen.local", "whatever123")
    assert response.status_code == 200
    assert b"Invalid email or password." in response.data


# 6. Logout -------------------------------------------------------------------

def test_logout_ends_session(client, student_user):
    login(client, student_user["email"], student_user["password"])
    assert client.get("/orders").status_code == 200  # confirms logged in

    response = logout(client)
    assert response.status_code == 200
    assert b"You have been logged out." in response.data

    # Protected routes must redirect to login again after logout.
    protected = client.get("/orders", follow_redirects=False)
    assert protected.status_code == 302
    assert "/login" in protected.headers["Location"]
