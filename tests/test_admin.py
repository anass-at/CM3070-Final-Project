"""Tests for /api/v1/admin endpoints (user/company management, access logs)."""
from unittest.mock import patch


def test_admin_get_stats(client, admin_token, citizen, company):
    r = client.get("/api/v1/admin/stats", headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
    data = r.json()
    assert data["total_companies"] == 1
    assert data["pending_companies"] == 1
    assert data["approved_companies"] == 0


def test_verify_user(client, admin_token, citizen, db):
    citizen.is_verified = False
    db.commit()
    r = client.post(
        f"/api/v1/admin/users/{citizen.id}/verify",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 200
    assert r.json()["is_verified"] is True


def test_reject_user(client, admin_token, citizen):
    r = client.post(
        f"/api/v1/admin/users/{citizen.id}/reject",
        json={"reason": "Document unclear"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["is_verified"] is False
    assert data["is_active"] is False
    assert data["rejection_reason"] == "Document unclear"


def test_approve_company_returns_oauth_credentials(client, admin_token, company):
    """T11 — Company receives OAuth 2.0 credentials upon admin approval."""
    with patch("app.api.routes.admin.create_hydra_client") as mock_create:
        mock_create.return_value = (f"company_{company.id}", "test_secret_xyz")
        r = client.post(
            f"/api/v1/admin/companies/{company.id}/approve",
            json={"scopes": ["name:legal"]},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
    assert r.status_code == 200
    data = r.json()
    assert data["hydra_client_id"] == f"company_{company.id}"
    assert data["hydra_client_secret"] == "test_secret_xyz"
    assert data["is_approved"] is True


def test_reject_company(client, admin_token, approved_company):
    with patch("app.api.routes.admin.delete_hydra_client"):
        r = client.post(
            f"/api/v1/admin/companies/{approved_company.id}/reject",
            json={"reason": "Fraudulent registration"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
    assert r.status_code == 200
    data = r.json()
    assert data["is_approved"] is False
    assert data["is_active"] is False


def test_approve_company_rejects_unregistered_scopes(client, admin_token, company):
    with patch("app.api.routes.admin.create_hydra_client"):
        r = client.post(
            f"/api/v1/admin/companies/{company.id}/approve",
            json={"scopes": ["profile:basic"]},   # company only requested name:legal
            headers={"Authorization": f"Bearer {admin_token}"},
        )
    assert r.status_code == 400


def test_admin_list_access_logs(client, admin_token):
    r = client.get("/api/v1/admin/access-logs", headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_citizen_cannot_access_admin_stats(client, citizen_token):
    """T9 — Standard citizen JWT rejected at /admin endpoints."""
    r = client.get("/api/v1/admin/stats", headers={"Authorization": f"Bearer {citizen_token}"})
    assert r.status_code == 403


def test_company_token_rejected_at_admin(client, company_token):
    """T10 — Standard company JWT rejected at /admin endpoints."""
    r = client.get("/api/v1/admin/stats", headers={"Authorization": f"Bearer {company_token}"})
    assert r.status_code == 403
