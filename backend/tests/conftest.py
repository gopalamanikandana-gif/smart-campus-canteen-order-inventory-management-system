import os

# Set test environment before application/database modules are imported.
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["JWT_SECRET"] = "test-secret"
os.environ["CANTEEN_OPEN_HOUR"] = "0"
os.environ["CANTEEN_CLOSE_HOUR"] = "24"

import pytest
from fastapi.testclient import TestClient

@pytest.fixture()
def client():
    from app.config import get_settings
    get_settings.cache_clear()

    from app.database import engine, Base
    from app.main import app

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    with TestClient(app) as test_client:
        yield test_client
