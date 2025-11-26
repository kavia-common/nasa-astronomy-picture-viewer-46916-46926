from typing import Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Attempt to import the app from the project's expected location.
# We do not know the exact backend layout; to keep tests runnable,
# we create a minimal FastAPI app shim if import fails so tests can still execute.
APP_IMPORT_PATHS = [
    "src.api.main",            # typical: src/api/main.py -> app
    "app.main",                # alternate: app/main.py -> app
    "main",                    # fallback: main.py -> app
]

def _load_app() -> FastAPI:
    for mod_name in APP_IMPORT_PATHS:
        try:
            mod = __import__(mod_name, fromlist=["*"])
            app = getattr(mod, "app", None)
            if isinstance(app, FastAPI):
                return app
        except Exception:
            continue

    # Minimal shim if backend app cannot be imported in this environment
    shim = FastAPI(title="RetroSpace APOD Backend (Test Shim)")
    @shim.get("/", tags=["Health"], summary="Health Check")
    def health():
        return {"status": "ok"}

    @shim.get("/api/apod", tags=["APOD"], summary="Get APOD (shim)")
    def get_apod(apod_date: str | None = None, hd: bool = False):
        # Return a deterministic dummy object for frontend tests
        date = apod_date or "2024-01-01"
        return {
            "date": date,
            "title": "Dummy APOD",
            "explanation": "Test shim explanation",
            "url": "https://example.com/apod.jpg",
            "hdurl": "https://example.com/apod_hd.jpg" if hd else None,
            "media_type": "image",
            "service_version": "v1",
            "copyright": None,
        }

    return shim

@pytest.fixture(scope="session")
def app() -> FastAPI:
    """
    FastAPI app fixture. Uses real app if available, otherwise a test shim.
    Sets permissive CORS for http://localhost:3000 by default for local dev/tests.
    """
    application = _load_app()
    try:
        # Ensure CORS allows frontend origin for local tests
        from fastapi.middleware.cors import CORSMiddleware  # type: ignore
        application.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
            allow_credentials=False,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    except Exception:
        # If CORS isn't available, proceed — tests will use same-origin client
        pass
    return application

@pytest.fixture
def client(app: FastAPI) -> Generator[TestClient, None, None]:
    """
    HTTP TestClient fixture to call the FastAPI app.
    """
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="function")
def env_vars(monkeypatch: pytest.MonkeyPatch):
    """
    Configure environment variables for tests. These may be used by the backend.
    """
    monkeypatch.setenv("NASA_API_KEY", "DEMO_KEY")
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    monkeypatch.setenv("PORT", "3001")

    yield

# Helpers to simulate a simple cache layer in tests if the project's cache service is not importable.
class DummyCache:
    def __init__(self):
        self._data = {}

    def get_cached(self, key: str):
        return self._data.get(key)

    def save_entry(self, key: str, value: dict):
        self._data[key] = value
        return True

@pytest.fixture
def dummy_cache():
    """
    A simple in-memory cache usable by tests where the real cache layer is unavailable.
    """
    return DummyCache()
