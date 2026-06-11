import pytest


def test_admin_can_list_users(client, seed_users, auth_headers):
    resp = client.get("/users/", headers=auth_headers["admin"])
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert body["total"] >= 4


def test_requester_cannot_list_users(client, seed_users, auth_headers):
    resp = client.get("/users/", headers=auth_headers["alice"])
    assert resp.status_code == 403


def test_admin_can_update_user_role(client, seed_users, auth_headers):
    bob_id = seed_users["bob"].id
    resp = client.patch(
        f"/users/{bob_id}",
        json={"role": "finance"},
        headers=auth_headers["admin"],
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == "finance"


def test_admin_cannot_update_own_account(client, seed_users, auth_headers):
    admin_id = seed_users["admin"].id
    resp = client.patch(
        f"/users/{admin_id}",
        json={"role": "manager"},
        headers=auth_headers["admin"],
    )
    assert resp.status_code == 400
    assert "own account" in resp.json()["detail"]


def test_admin_can_deactivate_user(client, seed_users, auth_headers):
    bob_id = seed_users["bob"].id
    resp = client.patch(
        f"/users/{bob_id}",
        json={"is_active": False},
        headers=auth_headers["admin"],
    )
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False


def test_update_nonexistent_user_returns_404(client, seed_users, auth_headers):
    resp = client.patch(
        "/users/99999",
        json={"role": "manager"},
        headers=auth_headers["admin"],
    )
    assert resp.status_code == 404
