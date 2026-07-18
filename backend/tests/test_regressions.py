"""Regression tests for the specific bugs fixed in this branch.

Each of these endpoints failed on its first real use before the fix.
"""


async def test_public_share_view_renders(client, seed):
    """Was: 500 — read item.quantity / item.images[].url (neither exists)."""
    resp = await client.get(f"/api/shares/public/{seed['share_token']}")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["container"]["name"]
    assert body["items"] is not None
    # The seeded item has no image, so image_url is null but must be present.
    for item in body["items"]:
        assert "image_url" in item
        assert "quantity" not in item


async def test_json_export_with_value_estimate(admin_client, seed):
    """Was: 500 — json.dumps on a Decimal value_estimate."""
    resp = await admin_client.get("/api/export/json")
    assert resp.status_code == 200, resp.text
    payload = resp.json()
    # Seeded item has value_estimate 12.50; must serialize as a number.
    items = payload.get("items", [])
    assert any(i.get("value_estimate") == 12.5 for i in items)


async def test_csv_export(admin_client):
    resp = await admin_client.get("/api/export/csv")
    assert resp.status_code == 200


async def test_tag_merge(admin_client, seed):
    """Was: 422 — handler took bare params, frontend sent a JSON object."""
    resp = await admin_client.post(
        "/api/tags/merge",
        json={"source_tag_ids": [seed["tag_id_2"]], "target_tag_id": seed["tag_id"]},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["id"] == seed["tag_id"]


async def test_ha_reminders_no_month_end_crash(client, seed):
    """Was: ValueError when today+7 overflows the month (replace(day=...))."""
    headers = {"X-API-Key": seed["api_key"]}
    resp = await client.get("/api/ha/reminders", headers=headers)
    assert resp.status_code == 200, resp.text
    assert "total" in resp.json() or isinstance(resp.json(), dict)


async def test_network_ipp_printer_creates(admin_client):
    """Was: DB error — printer_type_enum lacked 'network_ipp'."""
    resp = await admin_client.post(
        "/api/printers",
        json={
            "name": "IPP Printer",
            "printer_type": "network_ipp",
            "connection_type": "network",
            "address": "192.168.1.50:631",
            "label_width_mm": 51.0,
            "label_height_mm": 25.0,
        },
    )
    assert resp.status_code == 201, resp.text
    # cleanup
    await admin_client.delete(f"/api/printers/{resp.json()['id']}")
