from __future__ import annotations

import logging
import os
from datetime import date
from typing import Any

import httpx

from src.api.core.config import get_settings


NASA_APOD_URL = "https://api.nasa.gov/planetary/apod"

logger = logging.getLogger("nasa_client")


class NASAClientError(Exception):
    """Raised when NASA API returns an error or the request fails."""


class UpstreamTimeout(NASAClientError):
    """Raised when the NASA API request times out."""


class UpstreamRateLimited(NASAClientError):
    """Raised when the NASA API responds with HTTP 429 (rate limited)."""


def _resolve_timeout() -> float:
    """
    Determine request timeout in seconds from REQUEST_TIMEOUT_MS if provided,
    otherwise default to 20s.
    """
    raw = os.getenv("REQUEST_TIMEOUT_MS")
    if not raw:
        return 20.0
    try:
        ms = int(raw)
        if ms <= 0:
            return 20.0
        return ms / 1000.0
    except Exception:
        return 20.0


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
        UpstreamTimeout: If the request to NASA times out.
        UpstreamRateLimited: If NASA returns HTTP 429.
    """
    settings = get_settings()
    api_key = settings.nasa_api_key or "DEMO_KEY"

    params: dict[str, Any] = {
        "api_key": api_key,
        "hd": "true" if hd else "false",
    }
    if apod_date:
        params["date"] = apod_date.isoformat()

    timeout = _resolve_timeout()
    logger.info(
        "Calling NASA APOD",
        extra={"url": NASA_APOD_URL, "params": {k: v for k, v in params.items() if k != "api_key"}, "timeout_s": timeout},
    )

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            resp = await client.get(NASA_APOD_URL, params=params)
        except httpx.TimeoutException as e:
            logger.warning("NASA APOD request timed out", extra={"timeout_s": timeout})
            raise UpstreamTimeout(f"Network timeout contacting NASA API (timeout {timeout}s)") from e
        except httpx.HTTPError as e:
            logger.warning("NASA APOD network error", extra={"error": str(e)})
            raise NASAClientError(f"Network error contacting NASA API: {e}") from e

    if resp.status_code != 200:
        # Bubble up 4xx vs 5xx context for better error messages
        try:
            detail = resp.json()
        except Exception:
            detail = resp.text
        logger.error(
            "NASA APOD HTTP error",
            extra={"status": resp.status_code, "body": detail if isinstance(detail, dict) else str(detail)[:500]},
        )
        if resp.status_code == 400:
            # Invalid client input upstream (e.g., invalid date string)
            raise NASAClientError(f"Bad request to NASA API: {detail}")
        if resp.status_code == 429:
            raise UpstreamRateLimited("NASA API rate limit exceeded (HTTP 429)")
        raise NASAClientError(f"NASA API error {resp.status_code}: {detail}")

    try:
        data = resp.json()
    except ValueError as e:
        logger.error("NASA APOD invalid JSON")
        raise NASAClientError("Invalid JSON from NASA API") from e

    # Basic validation for expected fields
    required_fields = ["date", "title", "explanation", "media_type", "url"]
    if any(field not in data for field in required_fields):
        logger.error("NASA APOD missing expected fields", extra={"keys": list(data.keys())})
        raise NASAClientError("Missing expected fields from NASA API response")

    return data
