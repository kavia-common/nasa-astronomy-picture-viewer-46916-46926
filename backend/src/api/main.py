import logging
import os
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from src.api.core.config import get_settings
from src.api.core.dependencies import close_db_session
from src.api.routes.apod import router as apod_router

# PUBLIC_INTERFACE
def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application for RetroSpace APOD Viewer.

    - Loads environment-based settings
    - Configures CORS using ALLOWED_ORIGINS/REACT_* env vars with localhost defaults
    - Registers routes for APOD endpoints
    - Initializes database on startup and closes sessions on shutdown
    - Adds global error handling
    """
    # Load settings once (cached by get_settings), primarily for env validation
    get_settings()

    # Set default logging level to INFO if not explicitly configured
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO)
    else:
        logging.getLogger().setLevel(logging.INFO)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Startup
        from src.api.db import init_db
        init_db()
        yield
        # Shutdown
        close_db_session()

    app = FastAPI(
        title="RetroSpace APOD Backend",
        description="Backend service providing NASA Astronomy Picture of the Day data with cache-first logic.",
        version="1.0.0",
        lifespan=lifespan,
        openapi_tags=[
            {"name": "Health", "description": "Service health and readiness"},
            {"name": "APOD", "description": "Astronomy Picture of the Day endpoints"},
        ],
    )

    # CORS configuration
    # Priority order:
    # 1) ALLOWED_ORIGINS (comma-separated)
    # 2) REACT_* env vars if set
    # 3) localhost dev defaults
    allowed_origins: List[str] = []

    # Parse comma-separated list if provided
    allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
    if allowed_origins_env.strip():
        allowed_origins.extend([o.strip() for o in allowed_origins_env.split(",") if o.strip()])

    # Fall back to commonly provided frontend URL envs
    for var in ["REACT_APP_FRONTEND_URL", "REACT_APP_BACKEND_URL", "REACT_APP_API_BASE", "FRONTEND_URL"]:
        v = os.getenv(var)
        if v:
            allowed_origins.append(v.strip())

    # Always include common localhost origins for dev
    localhost_defaults = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://localhost:3000",
        "https://127.0.0.1:3000",
    ]
    for origin in localhost_defaults:
        if origin not in allowed_origins:
            allowed_origins.append(origin)

    # Remove duplicates while preserving order
    seen = set()
    allowed_origins = [o for o in allowed_origins if not (o in seen or seen.add(o))]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        # Explicit methods typical for browser/API use, ensures preflight correctness
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        # Allow commonly used headers; wildcard is ok but enumerate typical ones for clarity
        allow_headers=["*"],
        expose_headers=["*"],
    )

    # Health route
    @app.get("/", tags=["Health"], summary="Health Check")
    def health_check():
        """
        Health check endpoint to verify the service is running.

        Returns:
            dict: Simple message indicating health status.
        """
        return {"message": "Healthy"}

    # Register routers
    app.include_router(apod_router, prefix="/api")

    # Global error handler for unexpected exceptions
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_, exc: Exception):
        logging.exception("Unhandled error: %s", exc)
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    return app


app = create_app()

if __name__ == "__main__":
    # Local dev run
    import uvicorn

    settings = get_settings()
    port = int(os.getenv("PORT", str(settings.port)))
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=port, reload=True)
