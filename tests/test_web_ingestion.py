from pathlib import Path

import pytest

from app.ingestion.web import (
    UrlNotAllowedError,
    UrlSafetyError,
    WebFetchPolicy,
    extract_web_blocks,
    validate_url_for_fetch,
)


class FakeWebFetcher:
    def fetch_url_text(self, url: str, policy: WebFetchPolicy) -> tuple[str, dict]:
        final_url = validate_url_for_fetch(url, policy)
        return (
            "Refund policy allows cancellation within fourteen days.",
            {
                "url": url,
                "final_url": final_url,
                "title": "Refund Policy",
                "content_type": "text/html",
            },
        )


def test_validate_url_rejects_unsafe_schemes() -> None:
    policy = WebFetchPolicy()

    for url in [
        "file:///etc/passwd",
        "ftp://example.com/file.txt",
        "gopher://example.com",
        "data:text/plain,hello",
        "javascript:alert(1)",
    ]:
        with pytest.raises(UrlNotAllowedError):
            validate_url_for_fetch(url, policy)


def test_validate_url_rejects_local_and_private_networks() -> None:
    policy = WebFetchPolicy(allowed_schemes=("http", "https"))

    for url in [
        "http://localhost",
        "http://127.0.0.1",
        "http://0.0.0.0",
        "http://[::1]",
        "http://10.0.0.1",
        "http://172.16.0.10",
        "http://192.168.1.10",
        "http://169.254.169.254/latest/meta-data",
    ]:
        with pytest.raises(UrlSafetyError):
            validate_url_for_fetch(url, policy)


def test_validate_url_enforces_allowlist_and_blocklist() -> None:
    allow_policy = WebFetchPolicy(allowed_domains=("example.com",))
    assert validate_url_for_fetch("https://docs.example.com/page", allow_policy)

    with pytest.raises(UrlNotAllowedError):
        validate_url_for_fetch("https://other.example.org/page", allow_policy)

    block_policy = WebFetchPolicy(blocked_domains=("blocked.example",))
    with pytest.raises(UrlNotAllowedError):
        validate_url_for_fetch("https://sub.blocked.example/page", block_policy)


def test_extract_web_blocks_returns_normalized_connector_metadata() -> None:
    policy = WebFetchPolicy(allowed_domains=("example.com",))

    blocks = extract_web_blocks(
        url="https://example.com/refunds",
        policy=policy,
        fetcher=FakeWebFetcher(),
    )

    assert len(blocks) == 1
    assert "Title: Refund Policy" in blocks[0].text
    assert "Refund policy allows cancellation" in blocks[0].text
    assert blocks[0].metadata == {
        "source_type": "web",
        "url": "https://example.com/refunds",
        "final_url": "https://example.com/refunds",
        "title": "Refund Policy",
        "content_type": "text/html",
    }


def test_safe_fixture_directory_exists() -> None:
    assert Path("tests/fixtures/connectors").exists()
