from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser
from ipaddress import ip_address
from socket import getaddrinfo
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import ParseResult, urljoin, urlparse, urlunparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

from app.ingestion.types import ExtractedTextBlock


class UrlFetchError(RuntimeError):
    pass


class UrlNotAllowedError(RuntimeError):
    pass


class UrlSafetyError(RuntimeError):
    pass


@dataclass(frozen=True)
class WebFetchPolicy:
    allowed_schemes: tuple[str, ...] = ("https",)
    allowed_domains: tuple[str, ...] = ()
    blocked_domains: tuple[str, ...] = ()
    max_response_bytes: int = 2_000_000
    timeout_seconds: float = 10.0
    allow_private_ips: bool = False


class WebPageFetcher(Protocol):
    def fetch_url_text(
        self,
        url: str,
        policy: WebFetchPolicy,
    ) -> tuple[str, dict]: ...


class UrlLibWebPageFetcher:
    def fetch_url_text(
        self,
        url: str,
        policy: WebFetchPolicy,
    ) -> tuple[str, dict]:
        return fetch_url_text(url, policy)


class _NoRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: N802
        return None


class _ReadableHtmlParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._skip_depth = 0
        self._in_title = False
        self._title_parts: list[str] = []
        self._text_parts: list[str] = []

    @property
    def title(self) -> str | None:
        title = _collapse_whitespace(" ".join(self._title_parts))
        return title or None

    @property
    def text(self) -> str:
        return _collapse_whitespace(" ".join(self._text_parts))

    def handle_starttag(self, tag: str, attrs) -> None:
        del attrs
        normalized = tag.lower()
        if normalized in {"script", "style", "noscript"}:
            self._skip_depth += 1
        if normalized == "title":
            self._in_title = True
        if normalized in {"p", "br", "div", "section", "article", "li", "h1", "h2", "h3"}:
            self._text_parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        normalized = tag.lower()
        if normalized in {"script", "style", "noscript"} and self._skip_depth:
            self._skip_depth -= 1
        if normalized == "title":
            self._in_title = False
        if normalized in {"p", "div", "section", "article", "li", "h1", "h2", "h3"}:
            self._text_parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return

        stripped = data.strip()
        if not stripped:
            return

        if self._in_title:
            self._title_parts.append(stripped)

        self._text_parts.append(stripped)


def validate_url_for_fetch(url: str, policy: WebFetchPolicy) -> str:
    if not url or not url.strip():
        raise UrlSafetyError("URL is required.")

    parsed = urlparse(url.strip())

    if parsed.scheme.lower() not in policy.allowed_schemes:
        raise UrlNotAllowedError("URL scheme is not allowed.")

    if parsed.username or parsed.password:
        raise UrlSafetyError("URLs with embedded credentials are not allowed.")

    host = parsed.hostname
    if not host:
        raise UrlSafetyError("URL host is required.")

    normalized_host = host.lower().strip(".")

    if _domain_matches(normalized_host, policy.blocked_domains):
        raise UrlNotAllowedError("URL domain is blocked.")

    if policy.allowed_domains and not _domain_matches(normalized_host, policy.allowed_domains):
        raise UrlNotAllowedError("URL domain is not in the connector allowlist.")

    if not policy.allow_private_ips and _is_private_or_local_host(normalized_host):
        raise UrlSafetyError("Private or local network URLs are not allowed.")

    normalized = ParseResult(
        scheme=parsed.scheme.lower(),
        netloc=_normalized_netloc(parsed),
        path=parsed.path or "/",
        params=parsed.params,
        query=parsed.query,
        fragment="",
    )
    return urlunparse(normalized)


def fetch_url_text(
    url: str,
    policy: WebFetchPolicy,
) -> tuple[str, dict]:
    current_url = validate_url_for_fetch(url, policy)
    opener = build_opener(_NoRedirectHandler)

    for _ in range(5):
        request = Request(
            current_url,
            headers={"User-Agent": "rag-platform-connector/1.0"},
        )

        try:
            response = opener.open(request, timeout=policy.timeout_seconds)
        except HTTPError as exc:
            if exc.code in {301, 302, 303, 307, 308}:
                location = exc.headers.get("Location")
                if not location:
                    raise UrlFetchError(
                        "Redirect response did not include a Location header."
                    ) from exc
                current_url = validate_url_for_fetch(urljoin(current_url, location), policy)
                continue
            raise UrlFetchError(f"URL fetch failed with status {exc.code}.") from exc
        except URLError as exc:
            raise UrlFetchError(f"URL fetch failed: {exc.reason}") from exc

        final_url = validate_url_for_fetch(response.geturl(), policy)
        content_type = response.headers.get("Content-Type", "application/octet-stream")
        raw = response.read(policy.max_response_bytes + 1)
        response.close()

        if len(raw) > policy.max_response_bytes:
            raise UrlFetchError("URL response exceeded the maximum allowed size.")

        text, title = _decode_response(raw, content_type)

        if not text.strip():
            raise UrlFetchError("URL response did not contain readable text.")

        metadata = {
            "url": current_url,
            "final_url": final_url,
            "title": title,
            "content_type": content_type.split(";", 1)[0].strip().lower(),
        }
        return text, metadata

    raise UrlFetchError("URL redirected too many times.")


def extract_web_blocks(
    url: str,
    policy: WebFetchPolicy,
    fetcher: WebPageFetcher | None = None,
) -> list[ExtractedTextBlock]:
    active_fetcher = fetcher or UrlLibWebPageFetcher()
    text, metadata = active_fetcher.fetch_url_text(url, policy)
    title = metadata.get("title") or metadata.get("final_url") or metadata.get("url")
    display_url = metadata.get("final_url") or metadata.get("url") or url
    block_text = f"Title: {title}\nURL: {display_url}\n\n{text.strip()}"
    block_metadata = {
        "source_type": "web",
        "url": url,
        "final_url": display_url,
        "title": title,
        "content_type": metadata.get("content_type", "text/plain"),
    }

    return [
        ExtractedTextBlock(
            text=block_text,
            source_page=None,
            source_start_offset=0,
            source_end_offset=len(block_text),
            metadata=block_metadata,
        )
    ]


def _decode_response(raw: bytes, content_type: str) -> tuple[str, str | None]:
    charset = "utf-8"
    for part in content_type.split(";"):
        stripped = part.strip()
        if stripped.lower().startswith("charset="):
            charset = stripped.split("=", 1)[1].strip()

    decoded = raw.decode(charset, errors="replace")
    media_type = content_type.split(";", 1)[0].strip().lower()

    if media_type in {"text/html", "application/xhtml+xml"}:
        parser = _ReadableHtmlParser()
        parser.feed(decoded)
        return parser.text, parser.title

    return decoded.strip(), None


def _domain_matches(host: str, domains: tuple[str, ...]) -> bool:
    normalized_domains = [domain.lower().strip(".") for domain in domains if domain.strip()]
    return any(host == domain or host.endswith(f".{domain}") for domain in normalized_domains)


def _is_private_or_local_host(host: str) -> bool:
    if host in {"localhost", "0.0.0.0"} or host.endswith(".localhost"):
        return True

    try:
        return _is_private_ip(ip_address(host.strip("[]")))
    except ValueError:
        return False


def _is_private_ip(address) -> bool:
    return (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_reserved
        or address.is_multicast
        or address.is_unspecified
    )


def _normalized_netloc(parsed: ParseResult) -> str:
    host = (parsed.hostname or "").lower().strip(".")

    if ":" in host and not host.startswith("["):
        host = f"[{host}]"

    if parsed.port is not None:
        return f"{host}:{parsed.port}"

    return host


def _collapse_whitespace(value: str) -> str:
    return " ".join(value.split())


def resolve_host_is_private(host: str) -> bool:
    try:
        addresses = getaddrinfo(host, None)
    except OSError:
        return False

    return any(_is_private_ip(ip_address(address[4][0])) for address in addresses)
