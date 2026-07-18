"""Auth-lockdown regression tests.

These pin the fixes for the review's C1/C2/H1 findings: the API must not
let anonymous callers read inventory/PII or create/modify accounts, and
non-admins must not mutate other users.
"""

PROTECTED_GETS = [
    "/api/items",
    "/api/containers",
    "/api/locations",
    "/api/locations/stats",
    "/api/tags",
    "/api/search?q=x",
    "/api/search/autocomplete?q=x",
    "/api/inventory/tree",
    "/api/activity",
    "/api/printers",
    "/api/api-keys",
    "/api/webhooks",
    "/api/admin/stats",
]


async def test_protected_gets_reject_anonymous(client, seed):
    for path in PROTECTED_GETS:
        resp = await client.get(path)
        assert resp.status_code == 401, f"{path} should require auth, got {resp.status_code}"

    # Item/container/location detail routes need a concrete id.
    for path in (
        f"/api/items/{seed['item_id']}",
        f"/api/containers/{seed['container_id']}",
        f"/api/locations/{seed['location_id']}",
        f"/api/containers/{seed['container_id']}/path",
    ):
        resp = await client.get(path)
        assert resp.status_code == 401, f"{path} should require auth, got {resp.status_code}"


async def test_anonymous_cannot_create_admin(client):
    resp = await client.post(
        "/api/users",
        json={"name": "Sneaky", "role": "admin", "requires_password": False},
    )
    assert resp.status_code == 401


async def test_setup_is_closed_after_bootstrap(client):
    """The one-shot bootstrap must refuse once a user exists."""
    resp = await client.post(
        "/api/setup/complete",
        json={
            "admin_name": "Second Admin",
            "admin_email": "second@test.local",
            "admin_password": "pw",
        },
    )
    assert resp.status_code == 409


async def test_public_user_list_omits_pii(client):
    """The pre-login card grid is public but must not leak PII."""
    resp = await client.get("/api/users?include_admins=false&include_profiles=false")
    assert resp.status_code == 200
    for u in resp.json():
        assert "email" not in u
        assert "birthdate" not in u
        assert "role" not in u
        assert "name" in u and "id" in u


async def test_regular_user_cannot_modify_admin(user_client, seed):
    resp = await user_client.patch(
        f"/api/users/{seed['admin_id']}", json={"requires_password": False}
    )
    assert resp.status_code == 403


async def test_regular_user_cannot_delete_users(user_client, seed):
    resp = await user_client.delete(f"/api/users/{seed['admin_id']}")
    assert resp.status_code == 403


async def test_regular_user_can_update_self(user_client, seed):
    resp = await user_client.patch(
        f"/api/users/{seed['user_id']}", json={"name": "Renamed Self"}
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Renamed Self"


async def test_user_update_ignores_privilege_fields(admin_client, user_client, seed):
    """role/is_active are not part of the self-service schema."""
    resp = await user_client.patch(
        f"/api/users/{seed['user_id']}", json={"role": "admin"}
    )
    # Field is rejected by the schema (422) or simply ignored (200 + still user).
    assert resp.status_code in (200, 422)
    check = await admin_client.get(f"/api/users/{seed['user_id']}")
    assert check.json()["role"] == "user"


async def test_admin_cannot_delete_self(admin_client, seed):
    resp = await admin_client.delete(f"/api/users/{seed['admin_id']}")
    assert resp.status_code == 400
