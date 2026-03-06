from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.main import app


@pytest.fixture()
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


def test_validation_error_shape(client: TestClient) -> None:
    response = client.get("/parks/not-an-int")

    assert response.status_code == 422
    payload = response.json()
    assert payload["detail"] == "Request validation failed"
    assert payload["errors"]


def test_database_error_handler(client: TestClient, monkeypatch) -> None:
    from app.api.routes import parks

    def _boom(*_args, **_kwargs):
        raise SQLAlchemyError("db down")

    monkeypatch.setattr(parks, "get_parks", _boom)

    response = client.get("/parks")
    assert response.status_code == 500
    assert response.json() == {"detail": "Database operation failed"}
