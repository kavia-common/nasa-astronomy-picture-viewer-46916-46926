from datetime import date

import pytest
from fastapi.testclient import TestClient

from src.api.main import create_app
from src.api.db import init_db


@pytest.fixture(scope="module")
def client():
    init_db()
    app = create_app()
    with TestClient(app) as c:
        yield c


def test_health(client: TestClient):
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json().get("message") == "Healthy"


def test_apod_endpoint_today(monkeypatch, client: TestClient):
    from src.api.services import nasa_client

    async def fake_fetch(apod_date=None, hd=False):  # noqa: ANN001
        return {
            "date": date.today().isoformat(),
            "title": "Test Title",
            "explanation": "Test Explanation",
            "url": "http://example.com/image.jpg",
            "hdurl": "http://example.com/image_hd.jpg",
            "media_type": "image",
            "service_version": "v1",
        }

    monkeypatch.setattr(nasa_client, "fetch_apod", fake_fetch)

    r = client.get("/api/apod")
    assert r.status_code == 200
    body = r.json()
    assert body["title"] == "Test Title"
    assert body["media_type"] == "image"


def test_apod_endpoint_with_date(monkeypatch, client: TestClient):
    from src.api.services import nasa_client

    sample_date = date(2024, 1, 1)

    async def fake_fetch(apod_date=None, hd=False):  # noqa: ANN001
        assert apod_date == sample_date
        return {
            "date": sample_date.isoformat(),
            "title": "On Date",
            "explanation": "Explanation",
            "url": "http://example.com/dated.jpg",
            "hdurl": None,
            "media_type": "image",
            "service_version": "v1",
        }

    monkeypatch.setattr(nasa_client, "fetch_apod", fake_fetch)

    r = client.get(f"/api/apod?date={sample_date.isoformat()}&hd=true")
    assert r.status_code == 200
    body = r.json()
    assert body["date"] == sample_date.isoformat()
    assert body["title"] == "On Date"
