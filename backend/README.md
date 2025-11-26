# RetroSpace APOD Backend (FastAPI)

FastAPI backend providing NASA Astronomy Picture of the Day (APOD) with cache-first logic backed by SQLite.

## Features
- Cache-first DB→NASA logic (SQLite by default)
- NASA API integration using httpx (DEMO_KEY fallback)
- Pydantic schemas and SQLAlchemy models
- CORS enabled and environment-configurable
- Robust error handling
- OpenAPI docs at /docs
- Example unit tests

## Environment Variables
- NASA_API_KEY: NASA API key (defaults to DEMO_KEY if not set)
- DATABASE_URL: SQLAlchemy DB URL (defaults to sqlite:///./apod_cache.db)
- PORT: Server port (defaults to 3001)

Optional (affects CORS):
- REACT_APP_FRONTEND_URL
- REACT_APP_BACKEND_URL
- REACT_APP_API_BASE

You can create a `.env.example` illustrating variables.

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
