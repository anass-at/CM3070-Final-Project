"""Tests for /api/v1/company endpoints (registration, login, scope requests)."""
import json
from app.core.security import create_access_token

_REG = {
    "name": "Test Corp",
    "email": "corp@test.com",
    "password": "CompanyPass123!",
}


def _company_tok(company):
    return create_access_token({"sub": f"company_{company.id}", "scopes": [], "type": "company"})


def test_company_register_success(client):
    r = client.post("/api/v1/company/register", json=_REG)
    assert r.status_code == 201
    assert r.json()["email"] == _REG["email"]


def test_company_register_duplicate_email(client, company):
    r = client.post("/api/v1/company/register", json={**_REG, "email": company.email})
    assert r.status_code == 400


def test_company_login_success(client, company):
    r = client.post("/api/v1/company/login", json={"email": company.email, "password": "CompanyPass123!"})
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_company_login_wrong_password(client, company):
    r = client.post("/api/v1/company/login", json={"email": company.email, "password": "wrongpass"})
    assert r.status_code == 401


def test_company_get_profile(client, company):
    tok = _company_tok(company)
    r = client.get("/api/v1/company/profile", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 200
    assert r.json()["email"] == company.email


def test_request_scopes_success(client, company):
    tok = _company_tok(company)
    r = client.post(
        "/api/v1/company/request-scopes",
        json={"scopes": [{"scope": "name:legal", "justification": "KYC compliance requirement"}]},
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert r.status_code == 200
    scopes = r.json()["requested_scopes"]
    assert any(s["scope"] == "name:legal" for s in scopes)


def test_request_scopes_invalid_scope(client, company):
    tok = _company_tok(company)
    r = client.post(
        "/api/v1/company/request-scopes",
        json={"scopes": [{"scope": "invalid:scope", "justification": "anything"}]},
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert r.status_code == 400


def test_request_scopes_empty_justification_rejected(client, company):
    tok = _company_tok(company)
    r = client.post(
        "/api/v1/company/request-scopes",
        json={"scopes": [{"scope": "name:legal", "justification": "   "}]},
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert r.status_code == 400


def test_company_update_profile(client, company):
    tok = _company_tok(company)
    r = client.put(
        "/api/v1/company/profile",
        json={"company_type": "bank", "description": "A test bank"},
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert r.status_code == 200
    assert r.json()["company_type"] == "bank"


def test_company_logout(client, company):
    tok = _company_tok(company)
    r = client.post("/api/v1/company/logout", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 200
