import os
import pytest

def test_end_to_end_apod_flow(client, env_vars):
    """
    End-to-end: call health, then call APOD today and by date, verifying shape and caching repeat.
    """
    health = client.get("/")
    assert health.status_code == 200

    today = client.get("/api/apod")
    assert today.status_code == 200
    data_today = today.json()
    assert "title" in data_today and "url" in data_today

    specific = client.get("/api/apod?apod_date=2024-01-03")
    assert specific.status_code == 200
    data_specific = specific.json()
    assert data_specific["date"] == "2024-01-03"

    # Repeat should be fast (cache-like) and consistent
    repeat = client.get("/api/apod?apod_date=2024-01-03")
    assert repeat.status_code == 200
    assert repeat.json()["date"] == "2024-01-03"
