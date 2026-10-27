from pathlib import Path
import base64
import json
import sys
import types

import pytest

from src.core.config.curseforge_config_manager import CurseForgeConfigManager
from src.core.security.bundled_secrets import (
    seal_curseforge_api_key,
    unseal_Payload,
    unseal_bundled_curseforge_key,
)
from src.core.security.sensitive_data_redactor import SensitiveDataRedactor
from src.core.security.token_cipher import TokenCipher


class FakeDPAPI:
    CRYPTPROTECT_UI_FORBIDDEN = 1

    @staticmethod
    def CryptProtectData(data, description, entropy, reserved, prompt, flags):
        marker = base64.b64encode(entropy or b"")
        return marker + b"|" + bytes(data)

    @staticmethod
    def CryptUnprotectData(data, entropy, reserved, prompt, flags):
        marker, plaintext = bytes(data).split(b"|", 1)
        if marker != base64.b64encode(entropy or b""):
            raise ValueError("entropy mismatch")
        return "description", plaintext


def clear_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(CurseForgeConfigManager.ENV_API_KEY, raising=False)
    monkeypatch.delenv(CurseForgeConfigManager.ENV_GATEWAY_URL, raising=False)
    monkeypatch.delenv(CurseForgeConfigManager.ENV_CLIENT_TOKEN, raising=False)
    for index in range(1, CurseForgeConfigManager.MAX_GATEWAYS + 1):
        monkeypatch.delenv(f"{CurseForgeConfigManager.ENV_GATEWAY_URL_PREFIX}{index}", raising=False)
    monkeypatch.setattr(CurseForgeConfigManager, "DEFAULT_GATEWAY_URLS", ())
    monkeypatch.setattr(CurseForgeConfigManager, "DEFAULT_API_KEY", "")
    monkeypatch.setattr("src.core.config.curseforge_config_manager.unseal_bundled_curseforge_key", lambda: "")


def test_indexed_environment_gateways_and_token_have_priority(monkeypatch, tmp_path: Path) -> None:
    local = tmp_path / "curseforge_endpoints.json"
    local.write_text(json.dumps({"gateway_urls": ["https://local.example/api/curseforge"]}), encoding="utf-8")
    monkeypatch.setattr(CurseForgeConfigManager, "path", staticmethod(lambda: local))
    clear_environment(monkeypatch)
    monkeypatch.setenv(f"{CurseForgeConfigManager.ENV_GATEWAY_URL_PREFIX}1", "https://first.example/api/curseforge/")
    monkeypatch.setenv(f"{CurseForgeConfigManager.ENV_GATEWAY_URL_PREFIX}2", "https://second.example/api/curseforge")
    monkeypatch.setenv(CurseForgeConfigManager.ENV_CLIENT_TOKEN, "environment-token")

    assert CurseForgeConfigManager.gateway_urls() == (
        "https://first.example/api/curseforge",
        "https://second.example/api/curseforge",
    )
    assert CurseForgeConfigManager.gateway_url() == "https://first.example/api/curseforge"
    assert CurseForgeConfigManager.client_token() == "environment-token"


def test_five_local_gateways_are_encrypted_and_loaded(monkeypatch, tmp_path: Path) -> None:
    local = tmp_path / "private" / "curseforge_endpoints.json"
    clear_environment(monkeypatch)
    monkeypatch.setattr(CurseForgeConfigManager, "path", staticmethod(lambda: local))
    monkeypatch.setattr(TokenCipher, "_backend", FakeDPAPI)
    gateways = [f"https://gateway-{index}.example/api/curseforge/" for index in range(1, 6)]

    assert CurseForgeConfigManager.save_local(gateways, "client-token") == local
    assert CurseForgeConfigManager.gateway_urls() == tuple(value.rstrip("/") for value in gateways)
    assert CurseForgeConfigManager.client_token() == "client-token"

    payload = json.loads(local.read_text(encoding="utf-8"))
    assert payload["schema_version"] == CurseForgeConfigManager.SCHEMA_VERSION
    assert len(payload["protected_gateway_urls"]) == 5
    assert all(value.startswith(TokenCipher.PREFIX) for value in payload["protected_gateway_urls"])
    assert payload["protected_client_token"].startswith(TokenCipher.PREFIX)
    assert not any("gateway-" in value for value in payload["protected_gateway_urls"])


def test_legacy_plaintext_gateway_is_read_for_migration(monkeypatch, tmp_path: Path) -> None:
    local = tmp_path / "curseforge.json"
    clear_environment(monkeypatch)
    local.write_text(json.dumps({"gateway_url": "https://legacy.example/api/curseforge/"}), encoding="utf-8")
    monkeypatch.setattr(CurseForgeConfigManager, "path", staticmethod(lambda: local))

    assert CurseForgeConfigManager.gateway_urls() == ("https://legacy.example/api/curseforge",)


def test_empty_save_removes_private_config(monkeypatch, tmp_path: Path) -> None:
    local = tmp_path / "private" / "curseforge_endpoints.json"
    local.parent.mkdir(parents=True)
    local.write_text("{}", encoding="utf-8")
    clear_environment(monkeypatch)
    monkeypatch.setattr(CurseForgeConfigManager, "path", staticmethod(lambda: local))
    monkeypatch.setattr(TokenCipher, "_backend", FakeDPAPI)

    CurseForgeConfigManager.save_local([], "")

    assert local.exists() is False
    assert CurseForgeConfigManager.gateway_urls() == ()
    assert CurseForgeConfigManager.is_configured() is False


def test_gateway_requires_https_and_rejects_embedded_credentials() -> None:
    with pytest.raises(ValueError, match="HTTPS"):
        CurseForgeConfigManager._normalize_url("http://gateway.example/api/curseforge")
    with pytest.raises(ValueError, match="embedded credentials"):
        CurseForgeConfigManager._normalize_url("https://user:password@gateway.example/api/curseforge")


def test_save_rejects_more_than_five_nonempty_gateways(monkeypatch, tmp_path: Path) -> None:
    clear_environment(monkeypatch)
    monkeypatch.setattr(CurseForgeConfigManager, "path", staticmethod(lambda: tmp_path / "private" / "curseforge_endpoints.json"))
    monkeypatch.setattr(TokenCipher, "_backend", FakeDPAPI)

    with pytest.raises(ValueError, match="At most 5"):
        CurseForgeConfigManager.save_local(
            [f"https://gateway-{index}.example/api/curseforge" for index in range(1, 7)],
            "",
        )


def test_save_migrates_and_removes_legacy_plaintext_file(monkeypatch, tmp_path: Path) -> None:
    private = tmp_path / "private" / "curseforge_endpoints.json"
    legacy = tmp_path / "curseforge.json"
    legacy.write_text(
        json.dumps({"gateway_url": "https://legacy.example/api/curseforge", "client_token": "legacy-token"}),
        encoding="utf-8",
    )
    clear_environment(monkeypatch)
    monkeypatch.setattr(CurseForgeConfigManager, "path", staticmethod(lambda: private))
    monkeypatch.setattr(CurseForgeConfigManager, "legacy_path", staticmethod(lambda: legacy))
    monkeypatch.setattr(TokenCipher, "_backend", FakeDPAPI)

    CurseForgeConfigManager.save_local(["https://new.example/api/curseforge"])

    assert legacy.exists() is False
    assert CurseForgeConfigManager.gateway_urls() == ("https://new.example/api/curseforge",)
    assert CurseForgeConfigManager.client_token() == "legacy-token"


def test_no_gateway_is_used_when_no_override_exists(monkeypatch, tmp_path: Path) -> None:
    clear_environment(monkeypatch)
    monkeypatch.setattr(CurseForgeConfigManager, "path", staticmethod(lambda: tmp_path / "private" / "curseforge_endpoints.json"))
    monkeypatch.setattr(CurseForgeConfigManager, "legacy_path", staticmethod(lambda: tmp_path / "curseforge.json"))

    assert CurseForgeConfigManager.gateway_urls() == ()
    assert CurseForgeConfigManager.is_configured() is False
    with pytest.raises(ValueError, match="At least one CurseForge gateway URL"):
        CurseForgeConfigManager.gateway_url()


def test_default_gateway_url_is_used_when_no_local_config(monkeypatch, tmp_path: Path) -> None:
    clear_environment(monkeypatch)
    monkeypatch.setattr(CurseForgeConfigManager, "path", staticmethod(lambda: tmp_path / "private" / "curseforge_endpoints.json"))
    monkeypatch.setattr(CurseForgeConfigManager, "legacy_path", staticmethod(lambda: tmp_path / "curseforge.json"))
    monkeypatch.setattr(CurseForgeConfigManager, "DEFAULT_GATEWAY_URLS", ("https://gateway.example.com/api/curseforge",))

    assert CurseForgeConfigManager.gateway_urls() == ("https://gateway.example.com/api/curseforge",)
    assert CurseForgeConfigManager.is_configured() is True
    assert CurseForgeConfigManager.gateway_url() == "https://gateway.example.com/api/curseforge"


def test_curseforge_config_manager_encrypts_and_prioritizes_api_key(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    clear_environment(monkeypatch)
    config_file = tmp_path / "private" / "curseforge_endpoints.json"
    monkeypatch.setattr(CurseForgeConfigManager, "path", staticmethod(lambda: config_file))
    monkeypatch.setattr(CurseForgeConfigManager, "legacy_path", staticmethod(lambda: tmp_path / "curseforge.json"))
    monkeypatch.setattr(TokenCipher, "_backend", FakeDPAPI)

    # 1. When nothing configured, api_key() is empty
    assert CurseForgeConfigManager.api_key() == ""
    assert CurseForgeConfigManager.is_configured() is False

    # 2. Bundled key works when no custom key
    monkeypatch.setattr(CurseForgeConfigManager, "DEFAULT_API_KEY", "bundled-key-123")
    assert CurseForgeConfigManager.bundled_api_key() == "bundled-key-123"
    assert CurseForgeConfigManager.api_key() == "bundled-key-123"
    assert CurseForgeConfigManager.is_configured() is True

    # 3. Custom key encrypts and overrides bundled key
    CurseForgeConfigManager.save_api_key("custom-key-456")
    raw = json.loads(config_file.read_text(encoding="utf-8"))
    assert "protected_api_key" in raw
    assert "custom-key-456" not in config_file.read_text(encoding="utf-8")
    assert CurseForgeConfigManager.custom_api_key() == "custom-key-456"
    assert CurseForgeConfigManager.api_key() == "custom-key-456"

    # 4. Environment variable overrides both
    monkeypatch.setenv(CurseForgeConfigManager.ENV_API_KEY, "env-key-789")
    assert CurseForgeConfigManager.api_key() == "env-key-789"


def test_bundled_curseforge_key_sealing_and_unsealing_hides_plaintext(monkeypatch: pytest.MonkeyPatch) -> None:
    sample_key = "$2a$10$SyntheticUnitTestCurseForgeKey0123456789ABCDEFGHIJKLMN"
    module_source = seal_curseforge_api_key(sample_key)

    # Neither the raw key nor the "$2a$10$" prefix may appear in source or bytecode constants
    assert sample_key not in module_source
    assert "$2a$10$" not in module_source
    assert "CURSEFORGE" not in module_source.upper()

    code_obj = compile(module_source, "<_build_secrets>", "exec")
    for const in code_obj.co_consts:
        assert not (isinstance(const, str) and "$2a$" in const)

    namespace: dict[str, object] = {}
    exec(code_obj, namespace)

    fake_module = types.ModuleType("src._build_secrets")
    for attr in ("_S0", "_S1", "_S2", "_S3", "_S4"):
        setattr(fake_module, attr, namespace[attr])
    monkeypatch.setitem(sys.modules, "src._build_secrets", fake_module)

    assert unseal_bundled_curseforge_key() == sample_key

    # Tampering with any ciphertext byte must fail AES-GCM verification
    s4 = list(namespace["_S4"])  # type: ignore[arg-type]
    s4[0] ^= 0xFF
    with pytest.raises(Exception):
        unseal_Payload(
            namespace["_S0"],  # type: ignore[arg-type]
            namespace["_S1"],  # type: ignore[arg-type]
            namespace["_S2"],  # type: ignore[arg-type]
            namespace["_S3"],  # type: ignore[arg-type]
            tuple(s4),
        )


def test_sensitive_data_redactor_masks_curseforge_keys() -> None:
    sample_key = "$2a$10$SyntheticUnitTestCurseForgeKey0123456789ABCDEFGHIJKLMN"
    assert SensitiveDataRedactor.redact_text(f"Header x-api-key={sample_key} failed") == (
        f"Header x-api-key={SensitiveDataRedactor.REDACTED} failed"
    )
    assert SensitiveDataRedactor.redact_text(f"Raw key leaked: {sample_key}") == (
        f"Raw key leaked: {SensitiveDataRedactor.REDACTED}"
    )
    assert SensitiveDataRedactor.redact_value({"x-api-key": sample_key}) == {
        "x-api-key": SensitiveDataRedactor.REDACTED
    }
