"""Tests for /api/v1/auth endpoints (citizen registration, login, profile, password)."""

_REG = {
    "email": "new@test.com",
    "username": "newuser",
    "password": "Password123!",
    "first_name": "Alice",
    "last_name": "Smith",
    "national_id": "11223344",
}


def test_register_success(client):
    r = client.post("/api/v1/auth/register", json=_REG)
    assert r.status_code == 201
    data = r.json()
    assert data["email"] == _REG["email"]
    assert data["username"] == _REG["username"]
    assert "hashed_password" not in data


def test_register_duplicate_email(client, citizen):
    r = client.post("/api/v1/auth/register", json={**_REG, "email": citizen.email, "username": "other"})
    assert r.status_code == 400
    assert "Email" in r.json()["detail"]


def test_register_duplicate_username(client, citizen):
    r = client.post("/api/v1/auth/register", json={**_REG, "username": citizen.username, "email": "x@test.com"})
    assert r.status_code == 400
    assert "Username" in r.json()["detail"]


def test_register_national_id_must_be_8_digits(client):
    r = client.post("/api/v1/auth/register", json={**_REG, "national_id": "123"})
    assert r.status_code == 422


def test_login_success(client, citizen):
    r = client.post("/api/v1/auth/login", json={"email": citizen.email, "password": "Password123!"})
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_login_wrong_password(client, citizen):
    r = client.post("/api/v1/auth/login", json={"email": citizen.email, "password": "wrongpass"})
    assert r.status_code == 401


def test_me_returns_current_user(client, citizen, citizen_token):
    r = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {citizen_token}"})
    assert r.status_code == 200
    assert r.json()["email"] == citizen.email


def test_me_requires_auth(client):
    r = client.get("/api/v1/auth/me")
    assert r.status_code == 401


def test_update_profile(client, citizen, citizen_token):
    r = client.put(
        "/api/v1/auth/profile",
        json={"preferred_name": "Ali", "location": "Riyadh"},
        headers={"Authorization": f"Bearer {citizen_token}"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["preferred_name"] == "Ali"
    assert data["location"] == "Riyadh"


def test_logout_success(client, citizen_token):
    r = client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {citizen_token}"})
    assert r.status_code == 200


def test_change_password_success(client, citizen, citizen_token):
    r = client.put(
        "/api/v1/auth/change-password",
        json={"current_password": "Password123!", "new_password": "NewPassword456!"},
        headers={"Authorization": f"Bearer {citizen_token}"},
    )
    assert r.status_code == 200


def test_change_password_wrong_current(client, citizen, citizen_token):
    r = client.put(
        "/api/v1/auth/change-password",
        json={"current_password": "wrongpass", "new_password": "NewPassword456!"},
        headers={"Authorization": f"Bearer {citizen_token}"},
    )
    assert r.status_code == 400


def test_access_logs_returns_empty_list(client, citizen, citizen_token):
    r = client.get("/api/v1/auth/access-logs", headers={"Authorization": f"Bearer {citizen_token}"})
    assert r.status_code == 200
    assert r.json() == []
