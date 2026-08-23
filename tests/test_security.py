"""Unit tests for core security utilities (no HTTP, no DB)."""
import pytest
from jose import JWTError
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token


def test_hash_is_not_plain_text():
    h = hash_password("Secret123!")
    assert h != "Secret123!"
    assert h.startswith("$2b$") or h.startswith("$2a$")  # bcrypt prefix


def test_verify_correct_password():
    h = hash_password("Secret123!")
    assert verify_password("Secret123!", h) is True


def test_verify_wrong_password():
    h = hash_password("Secret123!")
    assert verify_password("WrongPassword", h) is False


def test_create_and_decode_token():
    token = create_access_token({"sub": "42"})
    payload = decode_access_token(token)
    assert payload["sub"] == "42"
    assert "exp" in payload


def test_decode_tampered_token_raises():
    token = create_access_token({"sub": "1"})
    tampered = token[:-4] + "XXXX"
    with pytest.raises(JWTError):
        decode_access_token(tampered)


def test_different_passwords_produce_different_hashes():
    assert hash_password("aaaa1234") != hash_password("aaaa1234")  # bcrypt salts
