import secrets
import requests
from app.core.config import settings


def create_hydra_client(company_id: int, approved_scopes: list) -> tuple:
    """
    Register a new OAuth2 client in Hydra for an approved company.
    Returns (client_id, client_secret) — secret is shown once, store it safely.
    """
    client_id = f"company_{company_id}"
    client_secret = secrets.token_urlsafe(32)

    resp = requests.post(
        f"{settings.HYDRA_ADMIN_URL}/admin/clients",
        json={
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_types": ["client_credentials", "authorization_code", "refresh_token"],
            "redirect_uris": ["http://localhost:5500/company/oauth-callback.html"],
            "response_types": ["code"],
            "scope": " ".join(approved_scopes),
            "token_endpoint_auth_method": "client_secret_post",
        },
        timeout=5,
    )
    resp.raise_for_status()
    return client_id, client_secret


def update_hydra_client(client_id: str, approved_scopes: list):
    """Update the scopes of an existing client (re-approval with different scopes)."""
    resp = requests.put(
        f"{settings.HYDRA_ADMIN_URL}/admin/clients/{client_id}",
        json={
            "client_id": client_id,
            "grant_types": ["client_credentials", "authorization_code", "refresh_token"],
            "redirect_uris": ["http://localhost:5500/company/oauth-callback.html"],
            "response_types": ["code"],
            "scope": " ".join(approved_scopes),
            "token_endpoint_auth_method": "client_secret_post",
        },
        timeout=5,
    )
    resp.raise_for_status()


def delete_hydra_client(client_id: str):
    """Remove a company's OAuth2 client when rejected."""
    resp = requests.delete(
        f"{settings.HYDRA_ADMIN_URL}/admin/clients/{client_id}",
        timeout=5,
    )
    if resp.status_code not in (204, 404):
        resp.raise_for_status()


def introspect_token(token: str) -> dict:
    """
    Ask Hydra if a token is valid. Returns dict with:
      active, scope, client_id, sub, exp, iat
    """
    resp = requests.post(
        f"{settings.HYDRA_ADMIN_URL}/admin/oauth2/introspect",
        data={"token": token},
        timeout=5,
    )
    resp.raise_for_status()
    return resp.json()


def get_login_request(challenge: str) -> dict:
    resp = requests.get(
        f"{settings.HYDRA_ADMIN_URL}/admin/oauth2/auth/requests/login",
        params={"login_challenge": challenge},
        timeout=5,
    )
    resp.raise_for_status()
    return resp.json()


def accept_login_request(challenge: str, subject: str) -> str:
    """Returns the redirect_to URL Hydra wants the browser sent to."""
    resp = requests.put(
        f"{settings.HYDRA_ADMIN_URL}/admin/oauth2/auth/requests/login/accept",
        params={"login_challenge": challenge},
        json={"subject": subject, "remember": False},
        timeout=5,
    )
    resp.raise_for_status()
    return resp.json()["redirect_to"]


def reject_login_request(challenge: str, reason: str = "User cancelled") -> str:
    resp = requests.put(
        f"{settings.HYDRA_ADMIN_URL}/admin/oauth2/auth/requests/login/reject",
        params={"login_challenge": challenge},
        json={"error": "access_denied", "error_description": reason},
        timeout=5,
    )
    resp.raise_for_status()
    return resp.json()["redirect_to"]


def get_consent_request(challenge: str) -> dict:
    resp = requests.get(
        f"{settings.HYDRA_ADMIN_URL}/admin/oauth2/auth/requests/consent",
        params={"consent_challenge": challenge},
        timeout=5,
    )
    resp.raise_for_status()
    return resp.json()


def accept_consent_request(challenge: str, scopes: list) -> str:
    resp = requests.put(
        f"{settings.HYDRA_ADMIN_URL}/admin/oauth2/auth/requests/consent/accept",
        params={"consent_challenge": challenge},
        json={
            "grant_scope": scopes,
            "grant_access_token_audience": [],
            "remember": False,
            "session": {},
        },
        timeout=5,
    )
    resp.raise_for_status()
    return resp.json()["redirect_to"]


def exchange_authorization_code(client_id: str, client_secret: str, code: str, redirect_uri: str) -> dict:
    """Exchange an authorization code for tokens at Hydra's public token endpoint."""
    resp = requests.post(
        f"{settings.HYDRA_PUBLIC_URL}/oauth2/token",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": client_id,
            "client_secret": client_secret,
        },
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def reject_consent_request(challenge: str) -> str:
    resp = requests.put(
        f"{settings.HYDRA_ADMIN_URL}/admin/oauth2/auth/requests/consent/reject",
        params={"consent_challenge": challenge},
        json={"error": "access_denied", "error_description": "User denied access"},
        timeout=5,
    )
    resp.raise_for_status()
    return resp.json()["redirect_to"]
