"""Webhook event system: SSRF guard, delivery, CRUD emission, reminder scan.

The HTTP layer is patched throughout so no real outbound request is made.
"""

import uuid

import pytest
from sqlalchemy import select

from app.database import get_sync_db
from app.models.webhook import WebhookDelivery


# --- fake HTTP layer --------------------------------------------------------


class _FakeResponse:
    def __init__(self, status_code: int = 200, text: str = "ok"):
        self.status_code = status_code
        self.text = text


class _FakeSyncClient:
    calls: list[dict] = []

    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def post(self, url, content=None, headers=None):
        _FakeSyncClient.calls.append({"url": url, "content": content, "headers": headers})
        return _FakeResponse(200, "delivered")


class _FakeAsyncClient:
    calls: list[dict] = []

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def post(self, url, content=None, headers=None):
        _FakeAsyncClient.calls.append({"url": url, "headers": headers})
        return _FakeResponse(200, "delivered")


# --- SSRF guard at create time ---------------------------------------------


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/hook",               # loopback
        "http://169.254.169.254/latest/meta",  # cloud metadata
        "http://[::1]/hook",                    # ipv6 loopback
        "ftp://example.com/hook",               # bad scheme
        "notaurl",                              # no scheme/host
    ],
)
async def test_create_rejects_internal_or_bad_urls(admin_client, url):
    r = await admin_client.post(
        "/api/webhooks",
        json={"name": "bad", "url": url, "events": ["item.created"]},
    )
    assert r.status_code == 422, f"{url} should be rejected, got {r.status_code}"


async def test_create_allows_lan_target(admin_client):
    """A LAN Home Assistant target (private IP) is the primary use case."""
    r = await admin_client.post(
        "/api/webhooks",
        json={
            "name": "lan",
            "url": "http://10.0.0.50:8123/api/webhook/xyz",
            "events": ["item.created"],
        },
    )
    assert r.status_code == 201, r.text
    await admin_client.delete(f"/api/webhooks/{r.json()['id']}")


# --- management lifecycle (test delivery patched) ---------------------------


async def test_webhook_lifecycle(admin_client, monkeypatch):
    import app.services.webhook_service as svc

    _FakeAsyncClient.calls.clear()
    monkeypatch.setattr(svc.httpx, "AsyncClient", _FakeAsyncClient)

    r = await admin_client.post(
        "/api/webhooks",
        json={
            "name": "hook",
            "url": "https://example.com/hook",
            "secret": "s3cr3t",
            "events": ["item.created", "item.updated"],
        },
    )
    assert r.status_code == 201, r.text
    wid = r.json()["id"]

    r = await admin_client.get(f"/api/webhooks/{wid}")
    assert r.status_code == 200

    r = await admin_client.patch(f"/api/webhooks/{wid}", json={"is_active": False})
    assert r.status_code == 200

    r = await admin_client.post(f"/api/webhooks/{wid}/test", json={"event": "item.created"})
    assert r.status_code == 200, r.text
    assert r.json()["success"] is True
    assert len(_FakeAsyncClient.calls) == 1

    r = await admin_client.get(f"/api/webhooks/{wid}/deliveries")
    assert r.status_code == 200 and len(r.json()) >= 1

    r = await admin_client.delete(f"/api/webhooks/{wid}")
    assert r.status_code in {200, 204}


# --- delivery task ----------------------------------------------------------


async def test_deliver_event_records_success(admin_client, monkeypatch):
    import app.services.webhook_delivery as wd

    _FakeSyncClient.calls.clear()
    monkeypatch.setattr(wd.httpx, "Client", _FakeSyncClient)

    r = await admin_client.post(
        "/api/webhooks",
        json={
            "name": "deliver",
            "url": "http://10.0.0.77:9000/hook",
            "secret": "key",
            "events": ["item.created"],
        },
    )
    wid = r.json()["id"]

    delivered = wd.deliver_event("item.created", {"item_id": "abc", "name": "X"})
    assert delivered >= 1

    mine = [c for c in _FakeSyncClient.calls if "10.0.0.77" in c["url"]]
    assert mine, "delivery did not POST to the webhook URL"
    assert "X-StorageHub-Signature" in mine[0]["headers"]  # HMAC applied

    with get_sync_db() as db:
        row = (
            db.execute(
                select(WebhookDelivery)
                .where(WebhookDelivery.webhook_id == uuid.UUID(wid))
                .order_by(WebhookDelivery.delivered_at.desc())
            )
            .scalars()
            .first()
        )
        assert row is not None
        assert row.success is True
        assert row.attempt_count == 1  # real count, not the old fabricated value

    await admin_client.delete(f"/api/webhooks/{wid}")


async def test_delivery_blocked_when_host_resolves_internal(admin_client, monkeypatch):
    """DNS-rebinding defense: a hostname that resolves to loopback is refused
    at delivery time and no HTTP request is made."""
    import app.services.webhook_delivery as wd
    import app.services.webhook_security as sec

    _FakeSyncClient.calls.clear()
    monkeypatch.setattr(wd.httpx, "Client", _FakeSyncClient)

    r = await admin_client.post(
        "/api/webhooks",
        json={"name": "rebind", "url": "http://sneaky.example/hook", "events": ["item.created"]},
    )
    wid = r.json()["id"]

    def _fake_getaddrinfo(host, port, *args, **kwargs):
        return [(2, 1, 6, "", ("127.0.0.1", port))]

    monkeypatch.setattr(sec.socket, "getaddrinfo", _fake_getaddrinfo)

    wd.deliver_event("item.created", {"x": 1})

    assert not any("sneaky" in c["url"] for c in _FakeSyncClient.calls)
    with get_sync_db() as db:
        row = (
            db.execute(
                select(WebhookDelivery).where(WebhookDelivery.webhook_id == uuid.UUID(wid))
            )
            .scalars()
            .first()
        )
        assert row is not None
        assert row.success is False
        assert "SSRF" in (row.response_body or "")

    await admin_client.delete(f"/api/webhooks/{wid}")


# --- CRUD emission ----------------------------------------------------------


async def test_item_crud_emits_events(admin_client, seed, monkeypatch):
    import app.worker.tasks as tasks

    recorded: list[tuple] = []
    monkeypatch.setattr(tasks.deliver_webhook_event, "delay", lambda *a, **k: recorded.append(a))

    r = await admin_client.post(
        "/api/items", json={"name": "Emit Item", "container_id": seed["container_id"]}
    )
    assert r.status_code == 201
    item_id = r.json()["id"]
    assert any(a[0] == "item.created" and a[1].get("item_id") == item_id for a in recorded)

    await admin_client.patch(f"/api/items/{item_id}", json={"name": "Emit2"})
    assert any(a[0] == "item.updated" for a in recorded)

    await admin_client.post(
        f"/api/items/{item_id}/move", params={"container_id": seed["child_container_id"]}
    )
    assert any(a[0] == "item.moved" for a in recorded)

    await admin_client.delete(f"/api/items/{item_id}")
    assert any(a[0] == "item.deleted" for a in recorded)


async def test_container_location_reminder_emit(admin_client, seed, monkeypatch):
    import app.worker.tasks as tasks

    recorded: list[tuple] = []
    monkeypatch.setattr(tasks.deliver_webhook_event, "delay", lambda *a, **k: recorded.append(a))

    r = await admin_client.post("/api/locations", json={"name": "Emit Loc"})
    loc = r.json()["id"]
    r = await admin_client.post("/api/containers", json={"name": "Emit Cont", "location_id": loc})
    cont = r.json()["id"]
    r = await admin_client.post(
        "/api/reminders",
        json={"title": "Emit Rem", "item_id": seed["item_id"], "due_date": "2030-01-01T00:00:00Z"},
    )
    rem = r.json()["id"]
    await admin_client.post(f"/api/reminders/{rem}/complete")

    events = {a[0] for a in recorded}
    assert "location.created" in events
    assert "container.created" in events
    assert "reminder.completed" in events

    await admin_client.delete(f"/api/reminders/{rem}")
    await admin_client.delete(f"/api/containers/{cont}")
    await admin_client.delete(f"/api/locations/{loc}")


# --- reminder scan ----------------------------------------------------------


async def test_scan_due_reminders_fires_once(admin_client, seed, monkeypatch):
    import app.services.webhook_delivery as wd

    fired: list[tuple] = []
    monkeypatch.setattr(
        wd, "deliver_event", lambda event, payload, user_id=None: fired.append((event, payload))
    )

    r = await admin_client.post(
        "/api/reminders",
        json={"title": "Past Due", "item_id": seed["item_id"], "due_date": "2000-01-01T00:00:00Z"},
    )
    assert r.status_code == 201
    rem_id = r.json()["id"]

    from app.worker.tasks import scan_due_reminders

    result = scan_due_reminders()
    assert result["due"] >= 1 and result["overdue"] >= 1
    events = [e for e, _ in fired]
    assert "reminder.due" in events and "reminder.overdue" in events
    assert any(p.get("reminder_id") == rem_id for _, p in fired)

    # Second scan must not re-fire the same reminder.
    fired.clear()
    scan_due_reminders()
    assert not any(p.get("reminder_id") == rem_id for _, p in fired)

    await admin_client.delete(f"/api/reminders/{rem_id}")
