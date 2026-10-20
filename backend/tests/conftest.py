"""Pytest configuration for backend tests.

Tests run against a separate MongoDB database (smart_ev_charging_test) so the
development database is never touched.
"""
import asyncio
import os

os.environ.setdefault("MONGODB_URI", "mongodb://root:changeme@localhost:27017/smart_ev_charging_test?authSource=admin")
os.environ.setdefault("MONGODB_DB", "smart_ev_charging_test")
os.environ.setdefault("APP_ENV", "test")

import pytest  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402

from app.main import app  # noqa: E402
import app.database as database_module  # noqa: E402


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


@pytest.fixture(autouse=True)
async def _clean_db():
    # Close any client leaked by the ASGI lifespan, then bind a fresh client
    # to the current event loop.
    await database_module.close_db()
    database_module._client = None
    database_module._db = None
    db = await database_module.connect_db()
    from app.database import init_indexes

    await init_indexes(db)
    for name in await db.list_collection_names():
        await db[name].delete_many({})
    yield
    await database_module.close_db()
