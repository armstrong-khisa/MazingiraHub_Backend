import pytest

from app import create_app
from extensions import db


@pytest.fixture()
def app(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    application = create_app()
    application.config.update(TESTING=True)

    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def register(client, email="donor@example.com", password="Secret123!"):
    return client.post(
        "/api/auth/register",
        json={
            "full_name": "Test Donor",
            "email": email,
            "password": password,
            "role": "donor",
        },
    )


def auth_headers(response):
    return {"Authorization": f"Bearer {response.json['access_token']}"}


@pytest.fixture()
def registered_client(client):
    return register(client)


@pytest.fixture()
def donor_headers(registered_client):
    return auth_headers(registered_client)
