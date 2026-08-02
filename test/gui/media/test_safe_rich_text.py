from src.gui.media.safe_rich_text import safe_external_url, sanitize_html


def test_sanitize_html_keeps_basic_formatting_and_safe_links() -> None:
    value = sanitize_html('<h2>Title</h2><script>alert(1)</script><a href="https://example.com/page">Open</a>')

    assert "<h2>Title</h2>" in value
    assert "<script" not in value
    assert "alert(1)" not in value
    assert '<a href="https://example.com/page">Open</a>' in value


def test_sanitize_html_removes_unsafe_link_targets() -> None:
    value = sanitize_html('<a href="javascript:alert(1)">Bad</a><img src="https://example.com/tracker.png">')

    assert "javascript:" not in value
    assert "<img" not in value
    assert value == "<a>Bad</a>"


def test_safe_external_url_accepts_only_credential_free_https() -> None:
    assert safe_external_url("https://example.com/project") == "https://example.com/project"
    assert safe_external_url("http://example.com/project") == ""
    assert safe_external_url("https://user:pass@example.com/project") == ""
    assert safe_external_url("file:///tmp/project") == ""
