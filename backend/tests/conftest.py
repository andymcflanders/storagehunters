"""Smoke-test harness.

Environment is configured BEFORE the app is imported so `get_settings()`
picks up the test values. Override DATABASE_URL / REDIS_URL in CI via
normal env vars.

Design notes:
- The app's async engine is swapped for a NullPool engine so connections
  never outlive a single request; this lets session-scoped seeding
  (asyncio.run in its own loop) coexist with function-scoped test loops.
- Every request passes through a coverage recorder that maps the concrete
  URL back to its route template. `test_zz_coverage.py` asserts every
  registered API route was exercised (or explicitly skipped).
"""

import asyncio
import os
import tempfile
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent

os.environ.setdefault(
    "DATABASE_URL", "postgresql://storagehub:storagehub@127.0.0.1:5432/storagehub_test"
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/9")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("AI_PROVIDER", "mock")
os.environ.setdefault("UPLOAD_DIR", tempfile.mkdtemp(prefix="storagehub-test-uploads-"))
os.environ.setdefault("FRONTEND_URL", "http://localhost")

import pytest  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine  # noqa: E402
from sqlalchemy.pool import NullPool  # noqa: E402

import app.database as database  # noqa: E402
from app.main import app  # noqa: E402

# --- Re-bind the app's engine to a NullPool so pooled connections are never
# --- reused across event loops (session-scoped seeding vs per-test loops).
_null_engine = create_async_engine(
    database.async_database_url,
    echo=False,
    future=True,
    poolclass=NullPool,
)
database.engine = _null_engine
database.async_session_maker = async_sessionmaker(
    _null_engine, class_=AsyncSession, expire_on_commit=False
)

# --- Coverage recording -----------------------------------------------------

import re  # noqa: E402

from tests._state import COVERED  # noqa: E402  (shared across modules)


def _build_template_matchers():
    """Compile OpenAPI path templates into (method, template, regex, specificity).

    Matching the concrete request path against these templates is robust to
    how the app nests routers internally. `specificity` (count of literal,
    non-`{param}` segments) lets us prefer e.g. `/reminders/upcoming` over
    `/reminders/{reminder_id}` when both match.
    """
    schema = app.openapi()
    matchers = []
    for template, ops in schema["paths"].items():
        regex = re.compile(
            "^" + re.sub(r"\{[^/}]+\}", r"[^/]+", template) + "$"
        )
        literal_segments = sum(
            1 for seg in template.split("/") if seg and not seg.startswith("{")
        )
        for method in ops:
            m = method.upper()
            if m in ("GET", "POST", "PATCH", "PUT", "DELETE"):
                matchers.append((m, template, regex, literal_segments))
    # /health is not in schema["paths"] for some apps; add defensively.
    matchers.append(("GET", "/health", re.compile(r"^/health$"), 1))
    # Most-specific first.
    matchers.sort(key=lambda x: x[3], reverse=True)
    return matchers


_TEMPLATE_MATCHERS = _build_template_matchers()


class _CoverageRecorder:
    """ASGI wrapper that records which (method, route-template) each request hit."""

    def __init__(self, wrapped):
        self.wrapped = wrapped

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            method = scope["method"]
            path = scope["path"]
            for m, template, regex, _spec in _TEMPLATE_MATCHERS:
                if m == method and regex.match(path):
                    COVERED.add((method, template))
                    break
        await self.wrapped(scope, receive, send)


_recording_app = _CoverageRecorder(app)

# --- Database bootstrap (once per session) ----------------------------------


def _reset_and_migrate() -> None:
    sync_url = os.environ["DATABASE_URL"]
    engine = create_engine(sync_url, isolation_level="AUTOCOMMIT")
    with engine.connect() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
    engine.dispose()

    from alembic import command
    from alembic.config import Config

    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    command.upgrade(cfg, "head")


ADMIN_EMAIL = "admin@test.local"
ADMIN_PASSWORD = "admin-test-password"

# Filled by _bootstrap(); read via the `seed` fixture.
SEED: dict = {}


def _make_client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=_recording_app), base_url="http://test")


async def _login_admin(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    assert resp.status_code == 200, f"admin login failed: {resp.status_code} {resp.text}"
    client.cookies.set("session_token", resp.json()["token"])


async def _login_user(client: AsyncClient, user_id: str) -> None:
    resp = await client.post("/api/auth/login", json={"user_id": user_id})
    assert resp.status_code == 200, f"user login failed: {resp.status_code} {resp.text}"
    client.cookies.set("session_token", resp.json()["token"])


async def _seed() -> None:
    """Create the admin (via the public one-shot setup) plus baseline data."""
    async with _make_client() as client:
        resp = await client.post(
            "/api/setup/complete",
            json={
                "admin_name": "Test Admin",
                "admin_email": ADMIN_EMAIL,
                "admin_password": ADMIN_PASSWORD,
                "admin_language": "en",
            },
        )
        assert resp.status_code == 200, f"setup failed: {resp.status_code} {resp.text}"
        SEED["admin_id"] = resp.json()["user"]["id"]

        await _login_admin(client)

        # Regular (non-admin, passwordless) household user
        resp = await client.post(
            "/api/users",
            json={"name": "Test User", "requires_password": False, "language": "en"},
        )
        assert resp.status_code == 201, resp.text
        SEED["user_id"] = resp.json()["id"]

        # Location -> container -> child container -> item
        resp = await client.post(
            "/api/locations", json={"name": "Test Garage", "description": "seed"}
        )
        assert resp.status_code == 201, resp.text
        SEED["location_id"] = resp.json()["id"]

        resp = await client.post(
            "/api/containers",
            json={"name": "Test Box", "location_id": SEED["location_id"]},
        )
        assert resp.status_code == 201, resp.text
        SEED["container_id"] = resp.json()["id"]
        SEED["container_qr"] = resp.json().get("qr_code")

        resp = await client.post(
            "/api/containers",
            json={
                "name": "Test Drawer",
                "location_id": SEED["location_id"],
                "parent_container_id": SEED["container_id"],
            },
        )
        assert resp.status_code == 201, resp.text
        SEED["child_container_id"] = resp.json()["id"]

        resp = await client.post(
            "/api/items",
            json={
                "name": "Test Wrench",
                "description": "a seeded wrench",
                "container_id": SEED["container_id"],
                "owner_id": SEED["user_id"],
                # exercises Decimal serialization in /api/export/json
                "value_estimate": 12.50,
            },
        )
        assert resp.status_code == 201, resp.text
        SEED["item_id"] = resp.json()["id"]

        # Tags: two so merge has a source and a target
        for key, name in (("tag_id", "seedtag"), ("tag_id_2", "seedtag2")):
            resp = await client.post("/api/tags", json={"name": name})
            assert resp.status_code == 201, resp.text
            SEED[key] = resp.json()["id"]

        # Share link for the container
        resp = await client.post(
            "/api/shares", json={"container_id": SEED["container_id"]}
        )
        assert resp.status_code == 201, resp.text
        SEED["share_id"] = resp.json()["id"]
        SEED["share_token"] = resp.json()["token"]

        # PDF printer (no hardware required)
        resp = await client.post(
            "/api/printers",
            json={
                "name": "Test PDF Printer",
                "printer_type": "generic_pdf",
                "connection_type": "file",
                "address": "/tmp/labels",
                "label_width_mm": 51.0,
                "label_height_mm": 25.0,
            },
        )
        assert resp.status_code == 201, resp.text
        SEED["printer_id"] = resp.json()["id"]

        # Reminder on the seeded item
        resp = await client.post(
            "/api/reminders",
            json={
                "title": "Seed reminder",
                "item_id": SEED["item_id"],
                "due_date": "2030-01-01T00:00:00Z",
            },
        )
        assert resp.status_code == 201, resp.text
        SEED["reminder_id"] = resp.json()["id"]

        # API key with all scopes (for /api/ha/* and key management tests)
        resp = await client.post(
            "/api/api-keys",
            json={"name": "seed key", "scopes": ["read", "write", "search", "webhooks"]},
        )
        assert resp.status_code == 201, resp.text
        SEED["api_key_id"] = resp.json()["id"]
        SEED["api_key"] = resp.json()["key"]


@pytest.fixture(scope="session", autouse=True)
def _bootstrap():
    _reset_and_migrate()
    asyncio.run(_seed())
    yield


@pytest.fixture()
def seed() -> dict:
    return SEED


@pytest.fixture()
async def client():
    """Unauthenticated client."""
    async with _make_client() as c:
        yield c


@pytest.fixture()
async def admin_client():
    """Client logged in as the admin (email + password)."""
    async with _make_client() as c:
        await _login_admin(c)
        yield c


@pytest.fixture()
async def user_client():
    """Client logged in as the regular passwordless household user."""
    async with _make_client() as c:
        await _login_user(c, SEED["user_id"])
        yield c
