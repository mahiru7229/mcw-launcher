from src.core.java.adoptium_client import AdoptiumClient


def test_selects_checksum_from_latest_assets_metadata():
    checksum = "a" * 64
    payload = [{
        "release_name": "jdk8u452-b09",
        "binary": {
            "architecture": "x64",
            "image_type": "jdk",
            "jvm_impl": "hotspot",
            "os": "windows",
            "package": {
                "checksum": checksum,
                "link": "https://example.test/OpenJDK8U-jdk_x64_windows_hotspot_8u452b09.zip",
                "name": "OpenJDK8U-jdk_x64_windows_hotspot_8u452b09.zip",
                "size": 123,
            },
        },
    }]

    asset, package = AdoptiumClient._select_package(payload, 8)

    assert asset["release_name"] == "jdk8u452-b09"
    assert AdoptiumClient._parse_sha256(package["checksum"], 8) == checksum


def test_supports_legacy_binaries_shape():
    payload = {
        "binaries": [{
            "architecture": "x64",
            "image_type": "jdk",
            "jvm_impl": "hotspot",
            "os": "windows",
            "package": {
                "checksum": "b" * 64,
                "link": "https://example.test/java-17.zip",
            },
        }],
    }

    _, package = AdoptiumClient._select_package(payload, 17)

    assert package["link"].endswith("java-17.zip")


def test_rejects_missing_checksum():
    try:
        AdoptiumClient._parse_sha256(None, 8)
    except RuntimeError as error:
        assert "missing" in str(error).lower()
    else:
        raise AssertionError("Missing checksum must be rejected")