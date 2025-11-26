from __future__ import annotations

from datetime import date as date_type
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.api.core.dependencies import get_db_session
from src.api.schemas import APODResponse
from src.api.services.cache import get_cached_apod, set_cached_apod
from src.api.services.nasa_client import fetch_apod, NASAClientError

router = APIRouter(prefix="/apod", tags=["APOD"])


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
        400: {"description": "Invalid input."},
        502: {"description": "Upstream NASA API error."},
        500: {"description": "Internal server error."},
    },
)
async def get_apod(
    apod_date: date_type | None = Query(default=None, description="YYYY-MM-DD date for APOD. Defaults to today."),
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
    """
    # If a specific date was provided, attempt to serve from cache first
    if apod_date is not None:
        cached = get_cached_apod(db, apod_date, hd)
        if cached:
            return cached

    # Fetch from NASA, then cache if possible
    try:
        data = await fetch_apod(apod_date, hd)
    except NASAClientError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e

    # If date is provided in response, cache it
    try:
        resp_date = data.get("date")
        if resp_date:
            # json date from NASA is str in ISO, ensure proper conversion in cache
            # set_cached_apod expects the 'date' string or date; SQLAlchemy model is Date type and will coerce
            set_cached_apod(db, data, hd)
    except Exception:
        # Cache errors should not fail the request; continue to return data
        pass

    return data
