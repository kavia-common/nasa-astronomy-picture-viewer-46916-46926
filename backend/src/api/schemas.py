from __future__ import annotations

from datetime import date as date_type
from pydantic import BaseModel, Field


class APODResponse(BaseModel):
    """
    Pydantic schema for APOD response payload.
    """
    date: date_type = Field(..., description="The date of the APOD.")
    title: str = Field(..., description="Title of the APOD content.")
    explanation: str = Field(..., description="Description/explanation of the content.")
    url: str = Field(..., description="URL of the content (image or video).")
    hdurl: str | None = Field(default=None, description="HD image URL when available.")
    media_type: str = Field(default="image", description="Type of media: image or video.")
    service_version: str | None = Field(default=None, description="API service version.")
    copyright: str | None = Field(default=None, description="Content copyright owner.")
    # Indicates that this payload is a local fallback due to upstream 429/timeout
    fallback: bool | None = Field(default=None, description="True if this APOD is a local fallback due to upstream limits.")


class APODQuery(BaseModel):
    """
    Pydantic schema for APOD query parameters.
    """
    # We keep field name 'date' but note that the route uses Query(alias="apod_date")
    date: date_type | None = Field(default=None, description="Specific date to request (YYYY-MM-DD).")
    hd: bool = Field(default=False, description="Request HD image if available.")
