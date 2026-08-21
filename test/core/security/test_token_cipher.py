from __future__ import annotations

import base64

import pytest

from src.core.security.token_cipher import TokenCipher
from src.core.fs.paths import Paths


class FakeDPAPI:
    CRYPTPROTECT_UI_FORBIDDEN = 1

    @staticmethod
    def CryptProtectData(data, description, entropy, reserved, prompt, flags):
        marker = base64.b64encode(entropy or b"").decode("ascii").encode("ascii")
        return marker + b"|" + bytes(data)

    @staticmethod
    def CryptUnprotectData(data, entropy, reserved, prompt, flags):
        marker, plaintext = bytes(data).split(b"|", 1)
        expected = base64.b64encode(entropy or b"").decode("ascii").encode("ascii")
        if marker != expected:
            raise ValueError("entropy mismatch")
        return "description", plaintext


def test_v2_cipher_uses_context_and_prefix(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(TokenCipher, "_backend", FakeDPAPI)

    protected = TokenCipher.encrypt("refresh-secret", "account:one:refresh")

    assert protected.startswith(TokenCipher.PREFIX)
    assert TokenCipher.decrypt(protected, "account:one:refresh") == "refresh-secret"
    with pytest.raises(RuntimeError, match="could not be unlocked"):
        TokenCipher.decrypt(protected, "account:two:refresh")


def test_cipher_reads_legacy_dpapi_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(TokenCipher, "_backend", FakeDPAPI)
    legacy_blob = FakeDPAPI.CryptProtectData(b"legacy-token", TokenCipher.LEGACY_DESCRIPTION, None, None, None, 0)
    legacy_value = base64.b64encode(legacy_blob).decode("ascii")

    assert TokenCipher.needs_upgrade(legacy_value)
    assert TokenCipher.decrypt(legacy_value, "ignored-purpose") == "legacy-token"


def test_portable_cipher_round_trip_is_bound_to_purpose(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    monkeypatch.setattr(TokenCipher, "_backend", None)
    monkeypatch.setattr(Paths, "CONFIG_ROOT", tmp_path / "config")

    protected = TokenCipher.encrypt("refresh-secret", "account:one:refresh")

    assert protected.startswith(TokenCipher.PORTABLE_PREFIX)
    assert TokenCipher.decrypt(protected, "account:one:refresh") == "refresh-secret"
    assert (Paths.CONFIG_ROOT / "private" / "credential.key").is_file()
    with pytest.raises(RuntimeError, match="could not be unlocked"):
        TokenCipher.decrypt(protected, "account:two:refresh")
