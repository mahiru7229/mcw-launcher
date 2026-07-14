import pytest

from src.core.java.java_major_policy import JavaMajorPolicy


def test_resolve_supported_buckets() -> None:
    assert JavaMajorPolicy.resolve(None) == 8
    assert JavaMajorPolicy.resolve(8) == 8
    assert JavaMajorPolicy.resolve(11) == 17
    assert JavaMajorPolicy.resolve(17) == 17
    assert JavaMajorPolicy.resolve(21) == 25
    assert JavaMajorPolicy.resolve(25) == 25


def test_rejects_newer_unsupported_java() -> None:
    with pytest.raises(RuntimeError):
        JavaMajorPolicy.resolve(26)
