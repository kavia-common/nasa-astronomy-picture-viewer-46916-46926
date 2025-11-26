from __future__ import annotations

import logging
from datetime import date as date_type
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.api.core.dependencies import get_db_session
from src.api.schemas import APODResponse
from src.api.services.cache import get_cached_apod, set_cached_apod
from src.api.services.nasa_client import fetch_apod, NASAClientError

router = APIRouter(prefix="/apod", tags=["APOD"])

logger = logging.getLogger("apod")


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
        - On NASA upstream failure/timeouts returns 502 with descriptive message
        - If cache exists when upstream fails, returns cached entry instead (graceful fallback)
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
    except NASAClientError as e:
        # Graceful fallback: if date was provided and cache exists despite error, return it
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
        # Return descriptive 502
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
