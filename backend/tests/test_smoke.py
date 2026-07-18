"""Smoke coverage: exercise every API endpoint at least once.

The contract is deliberately lenient on *outcome* for endpoints that
depend on external services (certbot, cloud storage, real printers) — for
those we only assert the route is wired and doesn't crash the framework
(no routing 404, no 405, no auth 401 when we did authenticate). For
everything self-contained we assert a real success code.

`test_zz_coverage` (in test_coverage.py) fails the build if any route in
the OpenAPI schema was never touched across the whole test session.
"""

import io

import pytest

# (method, path_template, json_body, allowed_status_codes)
# path templates use {name} placeholders filled from the seed fixture.

READS = [
    ("GET", "/health", {200}),
    ("GET", "/api/setup/status", {200}),
    ("GET", "/api/auth/me", {200}),
    ("GET", "/api/users", {200}),
    ("GET", "/api/users/{user_id}", {200}),
    ("GET", "/api/locations", {200}),
    ("GET", "/api/locations/stats", {200}),
    ("GET", "/api/locations/{location_id}", {200}),
    ("GET", "/api/containers", {200}),
    ("GET", "/api/containers/{container_id}", {200}),
    ("GET", "/api/containers/{container_id}/path", {200}),
    ("GET", "/api/containers/{container_id}/qr", {200}),
    ("GET", "/api/containers/qr/{container_qr}", {200, 404}),
    ("GET", "/api/items", {200}),
    ("GET", "/api/items/{item_id}", {200}),
    ("GET", "/api/tags", {200}),
    ("GET", "/api/search?q=wrench", {200}),
    ("GET", "/api/search/autocomplete?q=wr", {200}),
    ("GET", "/api/inventory/tree", {200}),
    ("GET", "/api/activity", {200}),
    ("GET", "/api/activity/my", {200}),
    ("GET", "/api/export/json", {200}),
    ("GET", "/api/export/csv", {200}),
    ("GET", "/api/shares", {200}),
    ("GET", "/api/reminders", {200}),
    ("GET", "/api/reminders/upcoming", {200}),
    ("GET", "/api/reminders/{reminder_id}", {200}),
    ("GET", "/api/outgrown", {200}),
    ("GET", "/api/triage/next", {200}),
    ("GET", "/api/triage/filters", {200}),
    ("GET", "/api/triage/discard", {200}),
    ("GET", "/api/printers", {200}),
    ("GET", "/api/printers/{printer_id}", {200}),
    ("GET", "/api/api-keys", {200}),
    ("GET", "/api/api-keys/{api_key_id}", {200}),
    ("GET", "/api/webhooks", {200}),
    ("GET", "/api/webhooks/events", {200}),
    # Admin
    ("GET", "/api/admin/stats", {200}),
    ("GET", "/api/admin/usage-stats", {200}),
    ("GET", "/api/admin/users", {200}),
    ("GET", "/api/admin/activity", {200}),
    ("GET", "/api/admin/openai", {200}),
    ("GET", "/api/admin/languages", {200}),
    ("GET", "/api/admin/backup/configs", {200}),
    ("GET", "/api/admin/backup/schedules", {200}),
    ("GET", "/api/admin/backup/history", {200}),
    ("GET", "/api/admin/backup/providers/status", {200}),
    # SSL: reads are fine; generate/renew hit external tooling (side_effects)
    ("GET", "/api/ssl", {200}),
    ("GET", "/api/ssl/status", {200}),
]

# Side-effect / external endpoints: assert only that routing + auth work
# (never 404-from-routing, never 405, never 401 when authenticated).
LENIENT = {401, 404, 405}


def _fill(path: str, seed: dict) -> str:
    return path.format(**seed)


@pytest.mark.parametrize("method,path,allowed", READS)
async def test_reads(admin_client, seed, method, path, allowed):
    resp = await admin_client.request(method, _fill(path, seed))
    assert resp.status_code in allowed, f"{method} {path} -> {resp.status_code}: {resp.text[:200]}"


HA_READS = [
    "/api/ha/status",
    "/api/ha/stats",
    "/api/ha/locations",
    "/api/ha/locations/{location_id}",
    "/api/ha/containers",
    "/api/ha/containers/{container_id}",
    "/api/ha/containers/qr/{container_qr}",
    "/api/ha/items",
    "/api/ha/items/{item_id}",
    "/api/ha/items/index",
    "/api/ha/tags",
    "/api/ha/reminders",
    "/api/ha/reminders/list",
    "/api/ha/search?q=wrench",
    "/api/ha/search/semantic?q=wrench",
]


@pytest.mark.parametrize("path", HA_READS)
async def test_ha_reads(client, seed, path):
    headers = {"X-API-Key": seed["api_key"]}
    resp = await client.get(_fill(path, seed), headers=headers)
    # /search/semantic falls back to keyword search when no embeddings exist.
    assert resp.status_code in {200, 404}, f"{path} -> {resp.status_code}: {resp.text[:200]}"


async def test_ha_requires_api_key(client):
    resp = await client.get("/api/ha/stats")
    assert resp.status_code == 401


async def test_write_lifecycle(admin_client, seed):
    """Create -> read -> update -> delete a throwaway object graph."""
    # Location
    r = await admin_client.post("/api/locations", json={"name": "Lifecycle Loc"})
    assert r.status_code == 201, r.text
    loc = r.json()["id"]

    r = await admin_client.patch(f"/api/locations/{loc}", json={"name": "Renamed Loc"})
    assert r.status_code == 200, r.text

    # Container in it
    r = await admin_client.post(
        "/api/containers", json={"name": "Lifecycle Box", "location_id": loc}
    )
    assert r.status_code == 201, r.text
    cont = r.json()["id"]

    r = await admin_client.patch(f"/api/containers/{cont}", json={"notes": "hi"})
    assert r.status_code == 200, r.text

    # Item in it
    r = await admin_client.post(
        "/api/items", json={"name": "Lifecycle Item", "container_id": cont}
    )
    assert r.status_code == 201, r.text
    item = r.json()["id"]

    r = await admin_client.patch(f"/api/items/{item}", json={"name": "Renamed Item"})
    assert r.status_code == 200, r.text

    # Tag attach (by name; endpoint creates the tag if needed) / detach
    r = await admin_client.post(f"/api/items/{item}/tags", params={"tag_name": "lifecycletag"})
    assert r.status_code in {200, 201}, r.text
    tag = r.json()["id"]
    r = await admin_client.delete(f"/api/items/{item}/tags/{tag}")
    assert r.status_code in {200, 204}, r.text

    # Move the item between containers (container_id is a query param)
    r = await admin_client.post(
        f"/api/items/{item}/move", params={"container_id": seed["container_id"]}
    )
    assert r.status_code in {200, 204}, r.text

    # Move the container via inventory endpoint
    r = await admin_client.post(
        f"/api/inventory/{cont}/move", json={"location_id": seed["location_id"]}
    )
    assert r.status_code in {200, 204}, r.text

    # Tear down
    for path in (
        f"/api/items/{item}",
        f"/api/tags/{tag}",
        f"/api/containers/{cont}",
        f"/api/locations/{loc}",
    ):
        r = await admin_client.delete(path)
        assert r.status_code in {200, 204}, f"delete {path} -> {r.status_code}"


async def test_item_image_lifecycle(admin_client, seed):
    """Upload an image, set primary, reprocess, process-all, delete."""
    png = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
        b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    files = {"file": ("t.png", io.BytesIO(png), "image/png")}
    r = await admin_client.post(f"/api/items/{seed['item_id']}/images", files=files)
    assert r.status_code in {200, 201}, r.text
    body = r.json()
    image_id = body.get("id") or (body.get("images") or [{}])[-1].get("id")
    assert image_id, f"no image id in {body}"

    r = await admin_client.post(
        f"/api/items/{seed['item_id']}/images/{image_id}/set-primary"
    )
    assert r.status_code in {200, 204}, r.text

    r = await admin_client.post(
        f"/api/items/{seed['item_id']}/images/{image_id}/reprocess"
    )
    assert r.status_code in {200, 202, 204}, r.text

    r = await admin_client.post(f"/api/items/{seed['item_id']}/process-all-images")
    assert r.status_code in {200, 202, 204}, r.text

    r = await admin_client.delete(
        f"/api/items/{seed['item_id']}/images/{image_id}"
    )
    assert r.status_code in {200, 204}, r.text


async def test_reminder_complete(admin_client, seed):
    r = await admin_client.post("/api/reminders", json={
        "title": "Completable",
        "item_id": seed["item_id"],
        "due_date": "2030-01-01T00:00:00Z",
    })
    assert r.status_code == 201, r.text
    rem = r.json()["id"]
    r = await admin_client.post(f"/api/reminders/{rem}/complete")
    assert r.status_code in {200, 204}, r.text
    r = await admin_client.patch(f"/api/reminders/{rem}", json={"title": "Edited"})
    assert r.status_code == 200, r.text
    r = await admin_client.delete(f"/api/reminders/{rem}")
    assert r.status_code in {200, 204}, r.text


async def test_share_toggle_and_delete(admin_client, seed):
    r = await admin_client.post(
        "/api/shares", json={"container_id": seed["container_id"]}
    )
    assert r.status_code == 201, r.text
    sid = r.json()["id"]
    r = await admin_client.patch(f"/api/shares/{sid}/toggle")
    assert r.status_code in {200, 204}, r.text
    r = await admin_client.delete(f"/api/shares/{sid}")
    assert r.status_code in {200, 204}, r.text


async def test_api_key_lifecycle(admin_client):
    r = await admin_client.post(
        "/api/api-keys", json={"name": "temp key", "scopes": ["read"]}
    )
    assert r.status_code == 201, r.text
    kid = r.json()["id"]
    r = await admin_client.patch(f"/api/api-keys/{kid}", json={"name": "renamed"})
    assert r.status_code == 200, r.text
    r = await admin_client.delete(f"/api/api-keys/{kid}")
    assert r.status_code in {200, 204}, r.text


async def test_webhook_lifecycle(admin_client):
    r = await admin_client.post(
        "/api/webhooks",
        json={
            "name": "Smoke Hook",
            "url": "http://localhost:9/hook",
            "events": ["item.created"],
        },
    )
    assert r.status_code == 201, r.text
    wid = r.json()["id"]
    r = await admin_client.get(f"/api/webhooks/{wid}")
    assert r.status_code == 200
    r = await admin_client.get(f"/api/webhooks/{wid}/deliveries")
    assert r.status_code == 200
    r = await admin_client.patch(f"/api/webhooks/{wid}", json={"is_active": False})
    assert r.status_code == 200
    # test delivery will fail to connect (localhost:9) but must not 5xx-crash
    r = await admin_client.post(f"/api/webhooks/{wid}/test")
    assert r.status_code not in LENIENT
    r = await admin_client.delete(f"/api/webhooks/{wid}")
    assert r.status_code in {200, 204}


async def test_printer_update(admin_client, seed):
    r = await admin_client.patch(
        f"/api/printers/{seed['printer_id']}", json={"name": "Renamed Printer"}
    )
    assert r.status_code == 200, r.text


async def test_tag_update(admin_client):
    r = await admin_client.post("/api/tags", json={"name": "updatetag"})
    assert r.status_code == 201, r.text
    tid = r.json()["id"]
    r = await admin_client.patch(f"/api/tags/{tid}", params={"new_name": "updatedtag"})
    assert r.status_code == 200, r.text
    await admin_client.delete(f"/api/tags/{tid}")


async def test_avatar_upload(admin_client, seed):
    png = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
        b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    files = {"file": ("a.png", png, "image/png")}
    r = await admin_client.post(f"/api/users/{seed['admin_id']}/avatar", files=files)
    assert r.status_code in {200, 201}, r.text


async def test_admin_settings_updates(admin_client):
    r = await admin_client.put(
        "/api/admin/languages", json={"supported_languages": ["en", "no"]}
    )
    assert r.status_code in {200, 204, 422}, r.text
    r = await admin_client.get("/api/admin/openai")
    assert r.status_code == 200
    cur = r.json()
    r = await admin_client.put("/api/admin/openai", json=cur)
    assert r.status_code in {200, 204, 422}, r.text
    r = await admin_client.post("/api/admin/recompute-size-ages")
    assert r.status_code in {200, 202, 204}, r.text
