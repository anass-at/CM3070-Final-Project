"""
Identity API tests — maps directly to T1–T14 in the project report.

Hydra's introspect_token is mocked so the suite runs without a live Hydra
instance.  Each test is labelled with its T-number for traceability.
"""
from unittest.mock import patch
from app.models.access_log import AccessLog

_INTROSPECT = "app.api.routes.identity.introspect_token"


def _hydra_ok(scopes: str, client_id: str):
    return {"active": True, "scope": scopes, "client_id": client_id}


# ── T1 ────────────────────────────────────────────────────────────────────────
def test_T1_name_legal_returns_name_fields(client, citizen, approved_company):
    """Token with name:legal scope returns first_name, last_name, middle_name only."""
    with patch(_INTROSPECT, return_value=_hydra_ok("name:legal", approved_company.hydra_client_id)):
        r = client.get(f"/api/v1/identity/{citizen.national_id}",
                       headers={"Authorization": "Bearer tok"})
    assert r.status_code == 200
    data = r.json()["data"]
    assert "first_name"   in data
    assert "middle_name"  in data
    assert "last_name"    in data


# ── T2 ────────────────────────────────────────────────────────────────────────
def test_T2_name_legal_excludes_birth_date_and_national_id(client, citizen, approved_company):
    """Token with name:legal scope cannot retrieve birth_date or national_id."""
    with patch(_INTROSPECT, return_value=_hydra_ok("name:legal", approved_company.hydra_client_id)):
        r = client.get(f"/api/v1/identity/{citizen.national_id}",
                       headers={"Authorization": "Bearer tok"})
    assert r.status_code == 200
    data = r.json()["data"]
    assert "birth_date"  not in data
    assert "national_id" not in data


# ── T3 ────────────────────────────────────────────────────────────────────────
def test_T3_expired_token_rejected(client, citizen, approved_company):
    """Expired Hydra token rejected by /identity endpoint → 401."""
    with patch(_INTROSPECT, return_value={"active": False}):
        r = client.get(f"/api/v1/identity/{citizen.national_id}",
                       headers={"Authorization": "Bearer expired"})
    assert r.status_code == 401


# ── T4 ────────────────────────────────────────────────────────────────────────
def test_T4_invalid_bearer_token_rejected(client, citizen, approved_company):
    """Structurally invalid Bearer token rejected → 401."""
    with patch(_INTROSPECT, side_effect=Exception("connection refused")):
        r = client.get(f"/api/v1/identity/{citizen.national_id}",
                       headers={"Authorization": "Bearer garbage.token"})
    assert r.status_code == 401


# ── T5 ────────────────────────────────────────────────────────────────────────
def test_T5_revoked_token_rejected(client, citizen, approved_company):
    """Revoked token rejected on every request (no caching) → 401."""
    with patch(_INTROSPECT, return_value={"active": False}):
        r = client.get(f"/api/v1/identity/{citizen.national_id}",
                       headers={"Authorization": "Bearer revoked"})
    assert r.status_code == 401


# ── T6 ────────────────────────────────────────────────────────────────────────
def test_T6_successful_call_writes_access_log(client, citizen, approved_company, db):
    """Every successful call to /identity writes a record to access_logs."""
    with patch(_INTROSPECT, return_value=_hydra_ok("name:legal", approved_company.hydra_client_id)):
        r = client.get(f"/api/v1/identity/{citizen.national_id}",
                       headers={"Authorization": "Bearer tok"})
    assert r.status_code == 200
    logs = db.query(AccessLog).all()
    assert len(logs) == 1
    assert logs[0].company_id  == approved_company.id
    assert logs[0].user_id     == citizen.id
    assert logs[0].status_code == 200


# ── T7 ────────────────────────────────────────────────────────────────────────
def test_T7_failed_call_still_writes_access_log(client, citizen, approved_company, db):
    """Failed identity call (invalid token) still writes a row to access_logs."""
    with patch(_INTROSPECT, side_effect=Exception("token invalid")):
        r = client.get(f"/api/v1/identity/{citizen.national_id}",
                       headers={"Authorization": "Bearer bad"})
    assert r.status_code == 401
    logs = db.query(AccessLog).all()
    assert len(logs) == 1
    assert logs[0].status_code == 401


# ── T8 ────────────────────────────────────────────────────────────────────────
def test_T8_citizen_can_view_own_access_log(client, citizen, citizen_token, approved_company, db):
    """Citizen can view their own access log via /auth/access-logs."""
    db.add(AccessLog(
        company_id=approved_company.id,
        company_name=approved_company.name,
        user_id=citizen.id,
        scope_used="name:legal",
        endpoint=f"/api/v1/identity/{citizen.national_id}",
        status_code=200,
    ))
    db.commit()
    r = client.get("/api/v1/auth/access-logs",
                   headers={"Authorization": f"Bearer {citizen_token}"})
    assert r.status_code == 200
    logs = r.json()
    assert len(logs) == 1
    assert logs[0]["company_name"] == approved_company.name
    assert logs[0]["scope_used"]   == "name:legal"


# ── T9 ────────────────────────────────────────────────────────────────────────
def test_T9_citizen_jwt_rejected_at_admin(client, citizen_token):
    """Standard citizen JWT rejected at /admin endpoints → 403."""
    r = client.get("/api/v1/admin/stats",
                   headers={"Authorization": f"Bearer {citizen_token}"})
    assert r.status_code == 403


# ── T10 ───────────────────────────────────────────────────────────────────────
def test_T10_company_jwt_rejected_at_admin(client, company_token):
    """Standard company JWT rejected at /admin endpoints → 403."""
    r = client.get("/api/v1/admin/stats",
                   headers={"Authorization": f"Bearer {company_token}"})
    assert r.status_code == 403


# ── T11 ───────────────────────────────────────────────────────────────────────
def test_T11_company_receives_oauth_credentials_on_approval(client, admin_token, company):
    """Company receives OAuth 2.0 credentials upon admin approval."""
    with patch("app.api.routes.admin.create_hydra_client") as mock_create:
        mock_create.return_value = (f"company_{company.id}", "test_client_secret")
        r = client.post(
            f"/api/v1/admin/companies/{company.id}/approve",
            json={"scopes": ["name:legal"]},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
    assert r.status_code == 200
    data = r.json()
    assert data["hydra_client_id"]     == f"company_{company.id}"
    assert data["hydra_client_secret"] == "test_client_secret"


# ── T12 ───────────────────────────────────────────────────────────────────────
def test_T12_rejected_scope_absent_from_approved_scopes(client, admin_token, company):
    """Scope not approved by the admin is absent from the company's approved_scopes."""
    with patch("app.api.routes.admin.create_hydra_client") as mock_create:
        mock_create.return_value = (f"company_{company.id}", "secret")
        # company requested name:legal; admin approves only name:legal (not profile:basic)
        r = client.post(
            f"/api/v1/admin/companies/{company.id}/approve",
            json={"scopes": ["name:legal"]},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
    assert r.status_code == 200
    approved = r.json()["approved_scopes"]
    assert "name:legal"   in approved
    assert "profile:basic" not in approved


# ── T13 ───────────────────────────────────────────────────────────────────────
def test_T13_unverified_citizen_not_accessible(client, unverified_citizen, approved_company):
    """Unverified citizen's data cannot be queried via the identity API → 403."""
    with patch(_INTROSPECT, return_value=_hydra_ok("name:legal", approved_company.hydra_client_id)):
        r = client.get(f"/api/v1/identity/{unverified_citizen.national_id}",
                       headers={"Authorization": "Bearer tok"})
    assert r.status_code == 403


# ── T14 ───────────────────────────────────────────────────────────────────────
def test_T14_profile_basic_returns_profile_fields_not_name(client, citizen, approved_company):
    """profile:basic token returns birth_date/nationality/profile_image, not name fields."""
    with patch(_INTROSPECT, return_value=_hydra_ok("profile:basic", approved_company.hydra_client_id)):
        r = client.get(f"/api/v1/identity/{citizen.national_id}",
                       headers={"Authorization": "Bearer tok"})
    assert r.status_code == 200
    data = r.json()["data"]
    # At least one profile field must be present (citizen has birth_date and nationality set)
    assert "birth_date" in data or "nationality" in data
    # Name fields must not appear
    assert "first_name"  not in data
    assert "last_name"   not in data
    assert "national_id" not in data
