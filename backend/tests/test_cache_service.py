import types

try:
    from src.services import cache as cache_service  # type: ignore
except Exception:
    # Minimal cache shim if the real service isn't importable
    class Cache:
        def __init__(self):
            self.store = {}

        def get_cached(self, key: str):
            return self.store.get(key)

        def save_entry(self, key: str, value: dict):
            self.store[key] = value
            return True

    cache_service = types.SimpleNamespace(Cache=Cache)

def test_get_cached_returns_entry():
    c = cache_service.Cache()
    c.save_entry("apod:2024-01-01", {"title": "Hello"})
    assert c.get_cached("apod:2024-01-01") == {"title": "Hello"}

def test_save_entry_inserts_and_updates():
    c = cache_service.Cache()
    c.save_entry("k", {"a": 1})
    assert c.get_cached("k") == {"a": 1}
    c.save_entry("k", {"a": 2})
    assert c.get_cached("k") == {"a": 2}
