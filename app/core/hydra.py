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
            "grant_types": ["client_credentials"],
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
            "grant_types": ["client_credentials"],
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
