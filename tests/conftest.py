"""
Shared pytest fixtures for the Smart Campus Canteen test suite.

IMPORTANT — DATABASE ISOLATION
-------------------------------
`config.py` builds SQLALCHEMY_DATABASE_URI from the DATABASE_URL environment
variable at *import time*. To guarantee the test suite never touches the
real `canteen.db`, we set DATABASE_URL to a throwaway temp-file SQLite
database BEFORE the `app` module (and therefore `config`) is imported.
Every test then runs against this isolated database, which is created
fresh for each test function and destroyed afterwards.
"""
import os
import sys
import tempfile

import pytest

# --- 1. Point the app at an isolated, throwaway SQLite file -----------------
_TEST_DB_FD, _TEST_DB_PATH = tempfile.mkstemp(prefix="test_canteen_", suffix=".db")
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB_PATH}"
os.environ.setdefault("SECRET_KEY", "test-secret-key")

# Make sure the project root (parent of tests/) is importable regardless of
# the directory pytest is invoked from.
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from werkzeug.security import generate_password_hash  # noqa: E402

from app import app as flask_app  # noqa: E402
from models import MenuItem, User, db  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _remove_test_db_file():
    """Delete the temp SQLite file once the whole test session finishes."""
    yield
    try:
        os.close(_TEST_DB_FD)
    except OSError:
        pass
    if os.path.exists(_TEST_DB_PATH):
        os.remove(_TEST_DB_PATH)


@pytest.fixture()
def app():
    """Flask app configured for testing, with a clean schema per test."""
    flask_app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{_TEST_DB_PATH}",
        SERVER_NAME="localhost.test",
        WTF_CSRF_ENABLED=False,
    )
    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    """Flask test client bound to the isolated test app/database."""
    return app.test_client()


# --- Helper functions (not fixtures themselves) -----------------------------

def login(client, email, password):
    return client.post(
        "/login",
        data={"email": email, "password": password},
        follow_redirects=True,
    )


def logout(client):
    return client.get("/logout", follow_redirects=True)


def create_user(name, email, password, role="student"):
    user = User(
        name=name,
        email=email,
        password_hash=generate_password_hash(password),
        role=role,
    )
    db.session.add(user)
    db.session.commit()
    return {"id": user.id, "name": name, "email": email, "password": password, "role": role}


def create_menu_item(name="Test Item", price=50.0, stock=10, is_available=True,
                      category="General", description="A test item"):
    item = MenuItem(
        name=name,
        description=description,
        category=category,
        price=price,
        stock=stock,
        is_available=is_available,
    )
    db.session.add(item)
    db.session.commit()
    return item.id


# --- Reusable fixtures --------------------------------------------------

@pytest.fixture()
def student_user(app):
    """Create a student account directly in the DB and return its credentials."""
    return create_user("Test Student", "student.test@canteen.local", "Student@123", role="student")


@pytest.fixture()
def second_student_user(app):
    """A second, distinct student account — used for cross-user isolation checks."""
    return create_user("Other Student", "other.student@canteen.local", "Other@123", role="student")


@pytest.fixture()
def admin_user(app):
    """Create an admin account directly in the DB and return its credentials."""
    return create_user("Test Admin", "admin.test@canteen.local", "Admin@123", role="admin")


@pytest.fixture()
def menu_item(app):
    """A single available menu item with stock=10, price=50.0."""
    item_id = create_menu_item(name="Masala Dosa", price=50.0, stock=10)
    return {"id": item_id, "name": "Masala Dosa", "price": 50.0, "stock": 10}


@pytest.fixture()
def low_stock_item(app):
    """A menu item with only 2 units in stock — for stock-limit tests."""
    item_id = create_menu_item(name="Limited Wrap", price=70.0, stock=2)
    return {"id": item_id, "name": "Limited Wrap", "price": 70.0, "stock": 2}


@pytest.fixture()
def out_of_stock_item(app):
    """An item flagged available but with zero stock."""
    item_id = create_menu_item(name="Sold Out Cake", price=40.0, stock=0, is_available=True)
    return {"id": item_id, "name": "Sold Out Cake", "price": 40.0, "stock": 0}


@pytest.fixture()
def unavailable_item(app):
    """An item explicitly marked unavailable (e.g. removed by admin)."""
    item_id = create_menu_item(name="Retired Snack", price=20.0, stock=5, is_available=False)
    return {"id": item_id, "name": "Retired Snack", "price": 20.0, "stock": 5}


@pytest.fixture()
def student_client(app, student_user):
    """Test client with its own session, logged in as the default student.

    Uses its own app.test_client() rather than the shared `client` fixture
    so that a test requesting both student_client and admin_client gets two
    independent cookie jars instead of one shared session.
    """
    c = app.test_client()
    login(c, student_user["email"], student_user["password"])
    return c


@pytest.fixture()
def admin_client(app, admin_user):
    """Test client with its own session, logged in as the default admin.

    See the note on student_client above regarding independent cookie jars.
    """
    c = app.test_client()
    login(c, admin_user["email"], admin_user["password"])
    return c
