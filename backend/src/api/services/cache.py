from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from src.api.models import APODCache


# PUBLIC_INTERFACE
def get_cached_apod(db: Session, apod_date: date, hd: bool) -> dict[str, Any] | None:
    """
    Retrieve a cached APOD entry from the database.

    Args:
        db: SQLAlchemy session.
        apod_date: Date of the APOD.
        hd: Whether HD version was requested.

    Returns:
        dict or None: Cached APOD data or None if not found.
    """
    row = (
        db.query(APODCache)
        .filter(APODCache.date == apod_date)
        .filter(APODCache.hd == (1 if hd else 0))
        .first()
    )
    if not row:
        return None

    data: dict[str, Any] = {
        "date": row.date,
        "title": row.title,
        "explanation": row.explanation,
        "url": row.url,
        "hdurl": row.hdurl,
        "media_type": row.media_type,
        "service_version": row.service_version,
        "copyright": row.copyright,
    }
    # If row is a fallback, include marker so callers can surface indicator
    if getattr(row, "is_fallback", 0):
        data["fallback"] = True
    return data


# PUBLIC_INTERFACE
def set_cached_apod(db: Session, apod: dict[str, Any], hd: bool) -> None:
    """
    Insert or update a cached APOD entry.

    Args:
        db: SQLAlchemy session.
        apod: Dict of APOD fields from NASA or a local fallback.
        hd: Whether HD version was requested.
    """
    date_val = apod.get("date")
    row = (
        db.query(APODCache)
        .filter(APODCache.date == date_val)
        .filter(APODCache.hd == (1 if hd else 0))
        .first()
    )
    is_fallback_flag = 1 if apod.get("fallback") else 0
    if row:
        row.title = apod.get("title", row.title)
        row.explanation = apod.get("explanation", row.explanation)
        row.url = apod.get("url", row.url)
        row.hdurl = apod.get("hdurl", row.hdurl)
        row.media_type = apod.get("media_type", row.media_type)
        row.service_version = apod.get("service_version", row.service_version)
        row.copyright = apod.get("copyright", row.copyright)
        # Update fallback marker if present
        if hasattr(row, "is_fallback"):
            row.is_fallback = is_fallback_flag
    else:
        row = APODCache(
            date=date_val,
            hd=1 if hd else 0,
            title=apod.get("title"),
            explanation=apod.get("explanation"),
            url=apod.get("url"),
            hdurl=apod.get("hdurl"),
            media_type=apod.get("media_type", "image"),
            service_version=apod.get("service_version"),
            copyright=apod.get("copyright"),
        )
        # Set fallback marker on insert if model supports it
        if hasattr(row, "is_fallback"):
            row.is_fallback = is_fallback_flag
        db.add(row)
    db.commit()
