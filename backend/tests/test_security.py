from datetime import timedelta

import pytest

from app.core.security import (
    create_access_token,
    decode_access_token,
    get_token_cipher,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    def test_hash_is_not_plaintext(self):
        hashed = hash_password("correct horse battery staple")
        assert hashed != "correct horse battery staple"

    def test_verify_correct_password_succeeds(self):
        hashed = hash_password("s3cr3t-password")
        assert verify_password("s3cr3t-password", hashed) is True

    def test_verify_incorrect_password_fails(self):
        hashed = hash_password("s3cr3t-password")
        assert verify_password("wrong-password", hashed) is False


class TestJWT:
    def test_round_trip(self):
        token = create_access_token(subject="user-123")
        assert decode_access_token(token) == "user-123"

    def test_expired_token_returns_none(self):
        token = create_access_token(subject="user-123", expires_delta=timedelta(seconds=-1))
        assert decode_access_token(token) is None

    def test_garbage_token_returns_none(self):
        assert decode_access_token("not-a-real-jwt") is None


class TestTokenCipher:
    def test_encrypt_decrypt_round_trip(self):
        cipher = get_token_cipher()
        plaintext = "spotify-access-token-abc123"
        encrypted = cipher.encrypt(plaintext)

        assert encrypted != plaintext
        assert cipher.decrypt(encrypted) == plaintext

    def test_decrypt_garbage_raises(self):
        cipher = get_token_cipher()
        with pytest.raises(ValueError):
            cipher.decrypt("not-a-valid-fernet-token")
