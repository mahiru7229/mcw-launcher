from __future__ import annotations

import hashlib
import hmac
import importlib
import os
from pathlib import Path

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from src.config import (
    CURSEFORGE_OFFICIAL_API_URL,
    DEVELOPER_NAME,
    GITHUB_REPOSITORY,
    LAUNCHER_SLUG,
    MICROSOFT_CLIENT_ID,
)

_PEPPER_TUPLES: tuple[int, ...] = (
    0x6D, 0x63, 0x77, 0x2D, 0x63, 0x66, 0x2D, 0x73,
    0x65, 0x61, 0x6C, 0x2D, 0x76, 0x31, 0x3A, 0x9E,
    0x37, 0x79, 0xB9, 0x7F, 0x4A, 0x7C, 0x15, 0xF3,
    0x9C, 0x06, 0x05, 0x73, 0x3D, 0xC2, 0x58, 0xE1,
)
_KDF_ITERATIONS = 12_000

_RUNTIME_PAD = os.urandom(64)
_CACHED_MASKED_KEY: bytes | None = None
_CACHED_SOURCE_FINGERPRINT: tuple[object, ...] | None = None


def _encode_tuple(raw: bytes, seed: int) -> tuple[int, ...]:
    return tuple(
        (byte ^ ((index * 73 + seed) & 0xFF)) & 0xFF
        for index, byte in enumerate(raw)
    )


def _decode_tuple(encoded: tuple[int, ...], seed: int) -> bytes:
    return bytes(
        (int(value) ^ ((index * 73 + seed) & 0xFF)) & 0xFF
        for index, value in enumerate(encoded)
    )


def _associated_data() -> bytes:
    context = f"{DEVELOPER_NAME}|{LAUNCHER_SLUG}|{GITHUB_REPOSITORY}|{CURSEFORGE_OFFICIAL_API_URL}"
    return hashlib.sha256(context.encode("utf-8")).digest()


def _derive_aes_key(salt: bytes, mask: bytes) -> bytes:
    context_bytes = f"{LAUNCHER_SLUG}:{MICROSOFT_CLIENT_ID}:{GITHUB_REPOSITORY}".encode("utf-8")
    material = hmac.new(bytes(_PEPPER_TUPLES), mask + context_bytes, hashlib.sha256).digest()
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=_KDF_ITERATIONS,
    )
    return kdf.derive(material)


def _xor_stream(data: bytes, mask: bytes, salt: bytes) -> bytes:
    out = bytearray(len(data))
    offset = 0
    counter = 0
    while offset < len(data):
        block = hmac.new(
            mask,
            salt + counter.to_bytes(4, "big"),
            hashlib.sha256,
        ).digest()
        chunk_len = min(len(block), len(data) - offset)
        for idx in range(chunk_len):
            out[offset + idx] = data[offset + idx] ^ block[idx]
        offset += chunk_len
        counter += 1
    return bytes(out)


def _mask_in_memory(raw: bytes) -> bytes:
    return bytes(
        byte ^ _RUNTIME_PAD[idx % len(_RUNTIME_PAD)]
        for idx, byte in enumerate(raw)
    )


def seal_curseforge_api_key(plaintext_key: str) -> str:
    cleaned = str(plaintext_key or "").strip()
    if not cleaned:
        raise ValueError("Cannot process an empty CurseForge API key.")
    if any(ch in cleaned for ch in ("\r", "\n", "\x00")):
        raise ValueError("CurseForge API key contains invalid control characters.")

    raw_bytes = cleaned.encode("utf-8")
    salt = os.urandom(16)
    nonce = os.urandom(12)
    mask = os.urandom(32)
    shard_a = os.urandom(32)
    shard_b = bytes(a ^ b for a, b in zip(mask, shard_a))

    whitened = _xor_stream(raw_bytes, mask, salt)
    aes_key = _derive_aes_key(salt, mask)
    ciphertext = AESGCM(aes_key).encrypt(nonce, whitened, _associated_data())

    s0 = _encode_tuple(salt, 0x35)
    s1 = _encode_tuple(nonce, 0x6B)
    s2 = _encode_tuple(shard_a, 0x9D)
    s3 = _encode_tuple(shard_b, 0xC4)
    s4 = _encode_tuple(ciphertext, 0x5A)

    return (
        f"_S0 = {s0!r}\n"
        f"_S1 = {s1!r}\n"
        f"_S2 = {s2!r}\n"
        f"_S3 = {s3!r}\n"
        f"_S4 = {s4!r}\n"
    )


def write_sealed_build_secrets(target: Path, plaintext_key: str) -> bool:
    cleaned = str(plaintext_key or "").strip()
    if not cleaned:
        return False
    source = seal_curseforge_api_key(cleaned)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source, encoding="utf-8")
    return True


def unseal_Payload(
    s0: tuple[int, ...],
    s1: tuple[int, ...],
    s2: tuple[int, ...],
    s3: tuple[int, ...],
    s4: tuple[int, ...],
) -> str:
    salt = _decode_tuple(tuple(s0), 0x35)
    nonce = _decode_tuple(tuple(s1), 0x6B)
    shard_a = _decode_tuple(tuple(s2), 0x9D)
    shard_b = _decode_tuple(tuple(s3), 0xC4)
    ciphertext = _decode_tuple(tuple(s4), 0x5A)

    if len(salt) != 16 or len(nonce) != 12 or len(shard_a) != 32 or len(shard_b) != 32:
        raise ValueError("Invalid build configuration dimensions.")

    mask = bytes(a ^ b for a, b in zip(shard_a, shard_b))
    aes_key = _derive_aes_key(salt, mask)
    whitened = AESGCM(aes_key).decrypt(nonce, ciphertext, _associated_data())
    plaintext_bytes = _xor_stream(whitened, mask, salt)
    value = plaintext_bytes.decode("utf-8").strip()
    if not value or any(ch in value for ch in ("\r", "\n", "\x00")):
        raise ValueError("Invalid CurseForge API key.")
    return value


def unseal_bundled_curseforge_key() -> str:
    global _CACHED_MASKED_KEY, _CACHED_SOURCE_FINGERPRINT
    try:
        module = importlib.import_module("src._build_secrets")
    except Exception:
        return ""

    s0 = getattr(module, "_S0", None)
    s1 = getattr(module, "_S1", None)
    s2 = getattr(module, "_S2", None)
    s3 = getattr(module, "_S3", None)
    s4 = getattr(module, "_S4", None)
    if all(isinstance(part, tuple) and part for part in (s0, s1, s2, s3, s4)):
        fingerprint = (s0, s1, s2, s3, s4)
        if _CACHED_MASKED_KEY is not None and _CACHED_SOURCE_FINGERPRINT == fingerprint:
            try:
                return _mask_in_memory(_CACHED_MASKED_KEY).decode("utf-8")
            except Exception:
                pass
        try:
            unsealed = unseal_Payload(s0, s1, s2, s3, s4)
            _CACHED_MASKED_KEY = _mask_in_memory(unsealed.encode("utf-8"))
            _CACHED_SOURCE_FINGERPRINT = fingerprint
            return unsealed
        except Exception:
            return ""

    legacy = getattr(module, "BUNDLED_CURSEFORGE_API_KEY", "")
    if isinstance(legacy, str) and legacy.strip():
        value = legacy.strip()
        if not any(ch in value for ch in ("\r", "\n", "\x00")):
            return value
    return ""
