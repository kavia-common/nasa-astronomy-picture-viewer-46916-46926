from __future__ import annotations

from datetime import date
from typing import Any

import httpx

from src.api.core.config import get_settings


NASA_APOD_URL = "https://api.nasa.gov/planetary/apod"


class NASAClientError(Exception):
    """Raised when NASA API returns an error or the request fails."""


# PUBLIC_INTERFACE
async def fetch_apod(apod_date: date | None = None, hd: bool = False) -> dict[str, Any]:
    """
    Fetch APOD data from NASA API.

    Args:
        apod_date: Optional date for which to fetch APOD. If None, fetch today's APOD.
        hd: Whether to request HD image if available.

    Returns:
        dict: JSON response from NASA API.

    Raises:
        NASAClientError: If the request fails or NASA API returns an error.
    """
    settings = get_settings()
    params: dict[str, Any] = {
        "api_key": settings.nasa_api_key or "DEMO_KEY",
        "hd": "true" if hd else "false",
    }
    if apod_date:
        params["date"] = apod_date.isoformat()

    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            resp = await client.get(NASA_APOD_URL, params=params)
        except httpx.HTTPError as e:
            raise NASAClientError(f"Network error contacting NASA API: {e}") from e

    if resp.status_code != 200:
        try:
            detail = resp.json()
        except Exception:
            detail = resp.text
        raise NASAClientError(f"NASA API error {resp.status_code}: {detail}")

    try:
        data = resp.json()
    except ValueError as e:
        raise NASAClientError("Invalid JSON from NASA API") from e

    # Basic validation for expected fields
    required_fields = ["date", "title", "explanation", "media_type", "url"]
    if any(field not in data for field in required_fields):
        raise NASAClientError("Missing expected fields from NASA API response")

    return data
