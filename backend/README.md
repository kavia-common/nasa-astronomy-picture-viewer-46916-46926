# RetroSpace APOD Backend (FastAPI)

FastAPI backend providing NASA Astronomy Picture of the Day (APOD) with cache-first logic backed by SQLite.

## Features
- Cache-first DB→NASA logic (SQLite by default)
- NASA API integration using httpx (DEMO_KEY fallback)
- Local fallback when NASA API is rate-limited (HTTP 429) or times out
- Pydantic schemas and SQLAlchemy models
- CORS enabled and environment-configurable
- Robust error handling
- OpenAPI docs at /docs
- Example unit tests

## Environment Variables
- NASA_API_KEY: NASA API key (defaults to DEMO_KEY if not set)
- DATABASE_URL: SQLAlchemy DB URL (defaults to sqlite:///./apod_cache.db)
- PORT: Server port (defaults to 3001)
- REQUEST_TIMEOUT_MS: Optional timeout for outbound NASA API calls in milliseconds (default 20000)
- ENABLE_UPSTREAM_FALLBACK: Enable local fallback when NASA API is rate-limited or times out. Accepts true/false/1/0 (default true)

Optional (affects CORS):
- ALLOWED_ORIGINS: Comma-separated list of allowed origins (overrides others).
- REACT_APP_FRONTEND_URL
- REACT_APP_BACKEND_URL
- REACT_APP_API_BASE

You can create a `.env.example` illustrating variables.

## Fallback Behavior
When NASA API responds with HTTP 429 (Too Many Requests) or times out:
1. If a cached entry exists for the requested date, the backend returns the cached entry.
2. If no cache entry exists and ENABLE_UPSTREAM_FALLBACK is true (default), the backend returns a deterministic local fallback APOD JSON with:
   - media_type: image
   - fallback: true
   - title/explanation indicating a fallback
   - url/hdurl pointing to a placeholder image
   The backend also attempts to save this fallback into the cache (marked with is_fallback in DB) to avoid repeated failures for the same day.
3. If ENABLE_UPSTREAM_FALLBACK is false, the backend returns HTTP 502 with an upstream error message.

Schema note: APODResponse includes an optional boolean field `fallback` to indicate when the payload is a local fallback.

## Run locally
- Install dependencies:
  pip install -r requirements.txt
- Start dev server:
  uvicorn src.api.main:app --host 0.0.0.0 --port 3001 --reload
  or simply:
  python -m src.api.main

## Endpoints
- GET / -> Health
- GET /api/apod?date=YYYY-MM-DD&hd=true|false -> APOD (cache-first)

## Generate OpenAPI spec
From project root of the backend container:
  python -m src.api.generate_openapi

## Testing
  pytest -q
