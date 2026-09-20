from __future__ import annotations

from unittest.mock import MagicMock, patch

from mcw_core.api.diagnostics.mclogs_client import McLogsClient, McLogsClientError


def test_empty_content_raises_error():
    try:
        McLogsClient.upload("")
        assert False, "Should have raised McLogsClientError"
    except McLogsClientError as e:
        assert "empty" in str(e).lower()

    try:
        McLogsClient.upload("   \n\t  ")
        assert False, "Should have raised McLogsClientError"
    except McLogsClientError as e:
        assert "empty" in str(e).lower()


def test_upload_success_redacts_sensitive_data():
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "success": True,
        "id": "test1234",
        "url": "https://mclo.gs/test1234",
        "raw": "https://api.mclo.gs/1/raw/test1234",
    }

    mock_client = MagicMock()
    mock_client.post.return_value = mock_response
    mock_client_context = MagicMock()
    mock_client_context.__enter__.return_value = mock_client
    mock_client_context.__exit__.return_value = None

    with patch("httpx.Client", return_value=mock_client_context):
        result = McLogsClient.upload("Minecraft crashed with session token=super_secret_access_token_xyz123")

    assert result["success"] is True
    assert result["id"] == "test1234"
    assert result["url"] == "https://mclo.gs/test1234"
    assert result["raw"] == "https://api.mclo.gs/1/raw/test1234"

    posted_content = mock_client.post.call_args[1]["data"]["content"]
    assert "super_secret_access_token_xyz123" not in posted_content
    assert "<redacted>" in posted_content


def test_upload_api_error_raises():
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "success": False,
        "error": "Log file is too long.",
    }

    mock_client = MagicMock()
    mock_client.post.return_value = mock_response
    mock_client_context = MagicMock()
    mock_client_context.__enter__.return_value = mock_client
    mock_client_context.__exit__.return_value = None

    with patch("httpx.Client", return_value=mock_client_context):
        try:
            McLogsClient.upload("some log content")
            assert False, "Should have raised McLogsClientError"
        except McLogsClientError as e:
            assert "Log file is too long" in str(e)


if __name__ == "__main__":
    test_empty_content_raises_error()
    test_upload_success_redacts_sensitive_data()
    test_upload_api_error_raises()
    print("test_mclogs_client passed!")
