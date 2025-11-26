from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.api.db import Base
from src.api.services.cache import get_cached_apod, set_cached_apod


def create_memory_session():
    engine = create_engine("sqlite:///:memory:", echo=False)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)
    return TestingSessionLocal()


def test_cache_set_and_get():
    db = create_memory_session()
    apod = {
        "date": date(2024, 5, 5),
        "title": "Title 1",
        "explanation": "Exp 1",
        "url": "http://example.com/1.jpg",
        "hdurl": "http://example.com/1_hd.jpg",
        "media_type": "image",
        "service_version": "v1",
    }
    set_cached_apod(db, apod, hd=True)
    got = get_cached_apod(db, apod_date=date(2024, 5, 5), hd=True)
    assert got is not None
    assert got["title"] == "Title 1"

    # Update path
    apod2 = apod | {"title": "Updated"}
    set_cached_apod(db, apod2, hd=True)
    got2 = get_cached_apod(db, apod_date=date(2024, 5, 5), hd=True)
    assert got2["title"] == "Updated"
