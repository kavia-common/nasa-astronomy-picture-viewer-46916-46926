from __future__ import annotations

import logging
import os
from datetime import date as date_type
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.api.core.dependencies import get_db_session
from src.api.schemas import APODResponse
from src.api.services.cache import get_cached_apod, set_cached_apod
from src.api.services.nasa_client import fetch_apod, NASAClientError, UpstreamRateLimited, UpstreamTimeout

router = APIRouter(prefix="/apod", tags=["APOD"])

logger = logging.getLogger("apod")


def _fallback_enabled() -> bool:
    """Check env var ENABLE_UPSTREAM_FALLBACK (default: true)."""
    val = os.getenv("ENABLE_UPSTREAM_FALLBACK", "true").strip().lower()
    return val in ("1", "true", "yes", "on")


def _build_fallback_payload(apod_date: date_type | None, hd: bool) -> dict[str, Any]:
    """
    Build a deterministic local fallback payload. Uses a bundled placeholder URL path.

    Note: The frontend is expected to handle media_type=image; url should be reachable.
    For now we provide a static path that the frontend can load or a generic placeholder.
    """
    # We don't have a static served asset path in this backend; use a generic placeholder
    # that renders in most environments. Frontend will display it as an image.
    placeholder_url = "https://via.placeholder.com/1024x768?text=RetroSpace+APOD+Unavailable"
    d = (apod_date or date_type.today()).isoformat()
    return {
        "date": d,
        "title": "RetroSpace Fallback APOD",
        "explanation": "NASA APOD is temporarily unavailable due to rate limiting or timeout. Showing a local fallback.",
        "url": placeholder_url,
        "hdurl": placeholder_url if hd else None,
        "media_type": "image",
        "service_version": "v1",
        "copyright": None,
        "fallback": True,
    }


@router.get(
    "",
    response_model=APODResponse,
    summary="Get APOD (Astronomy Picture of the Day)",
    description=(
        "Cache-first endpoint: attempts to serve from local DB cache; "
        "on cache miss, fetches from NASA API, stores in cache, and returns the result."
    ),
    responses={
        200: {"description": "APOD data."},
        400: {"description": "Invalid input (e.g., bad apod_date)."},
        502: {"description": "Upstream NASA API error (network/timeout/HTTP error)."},
        500: {"description": "Internal server error."},
    },
)
async def get_apod(
    apod_date: date_type | None = Query(
        default=None,
        alias="apod_date",
        description="YYYY-MM-DD date for APOD. Defaults to today.",
    ),
    hd: bool = Query(default=False, description="Request HD image if available."),
    db: Session = Depends(get_db_session),
) -> Any:
    """
    Retrieve APOD for a given date with cache-first logic.

    Parameters:
        apod_date (date, optional): Date of APOD. If not provided, NASA API returns today's APOD.
        hd (bool): Whether to request HD image.
        db (Session): Database session from dependency.

    Returns:
        APODResponse: APOD content for the requested date.

    Behavior:
        - Logs cache hit/miss at INFO
        - On NASA upstream failure/timeouts, return 502 unless fallback is enabled and cache miss
        - If cache exists when upstream fails, returns cached entry instead (graceful fallback)
        - If fallback is enabled and there is a cache miss and upstream is rate-limited/timeout,
          return a deterministic fallback JSON with fallback: true (and optionally cache it)
    """
    # Cache-first when a date is explicitly provided
    if apod_date is not None:
        cached = get_cached_apod(db, apod_date, hd)
        if cached:
            logger.info("APOD cache hit", extra={"apod_date": str(apod_date), "hd": hd})
            return cached
        logger.info("APOD cache miss", extra={"apod_date": str(apod_date), "hd": hd})

    # Fetch from NASA, then cache if possible
    try:
        data = await fetch_apod(apod_date, hd)
    except (UpstreamRateLimited, UpstreamTimeout) as e:
        # If cache exists, serve it regardless
        if apod_date is not None:
            cached = get_cached_apod(db, apod_date, hd)
            if cached:
                logger.warning(
                    "Upstream limited/timeout, serving cached APOD",
                    extra={"apod_date": str(apod_date), "hd": hd, "error": str(e)},
                )
                return cached

        # If fallback enabled and cache miss, return deterministic local fallback JSON (200)
        if _fallback_enabled():
            fallback_payload = _build_fallback_payload(apod_date, hd)
            logger.info(
                "Using local fallback APOD due to upstream limitation",
                extra={"apod_date": str(apod_date) if apod_date else None, "hd": hd},
            )
            # Optionally store fallback in DB to avoid repeated upstream failures for same day
            try:
                set_cached_apod(db, fallback_payload, hd)
            except Exception as cache_err:
                logger.warning("Failed to cache fallback APOD", extra={"error": str(cache_err)})
            return fallback_payload

        # Fallback disabled: surface 502
        logger.error(
            "Upstream limited/timeout; fallback disabled",
            extra={"apod_date": str(apod_date) if apod_date else None, "hd": hd, "error": str(e)},
        )
        raise HTTPException(
            status_code=502,
            detail={"message": "NASA API is rate limited or timed out", "upstream_error": str(e)},
        ) from e
    except NASAClientError as e:
        # Other upstream errors (non-429, non-timeout)
        if apod_date is not None:
            cached = get_cached_apod(db, apod_date, hd)
            if cached:
                logger.warning(
                    "Upstream NASA error, serving cached APOD",
                    extra={"apod_date": str(apod_date), "hd": hd, "error": str(e)},
                )
                return cached
        logger.error(
            "Upstream NASA API failure",
            extra={"apod_date": str(apod_date) if apod_date else None, "hd": hd, "error": str(e)},
        )
        raise HTTPException(
            status_code=502,
            detail={"message": "Failed to retrieve APOD from NASA API", "upstream_error": str(e)},
        ) from e

    # If date is provided in response, cache it
    try:
        resp_date = data.get("date")
        if resp_date:
            set_cached_apod(db, data, hd)
            logger.info(
                "APOD cached",
                extra={"apod_date": resp_date, "hd": hd, "title": data.get("title")},
            )
    except Exception as cache_err:
        # Cache errors should not fail the request; continue to return data
        logger.warning("Failed to write APOD to cache", extra={"error": str(cache_err)})

    return data
