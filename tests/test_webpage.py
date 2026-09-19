"""Webpage client and extraction tests with mocked network requests."""

import httpx
import pytest

from web_search_mcp.config import Settings
from web_search_mcp.errors import UpstreamError
from web_search_mcp.services.webpage_client import WebpageClient
from web_search_mcp.utils.extraction import extract_readable_text


def test_html_text_extraction_removes_scripts() -> None:
    text, title, truncated = extract_readable_text(
        "<html><title>Docs</title><script>secret()</script><p>Hello world</p></html>",
        max_characters=100,
    )
    assert title == "Docs"
    assert text == "Docs Hello world"
    assert "secret" not in text
    assert truncated is False


@pytest.mark.asyncio
async def test_successful_webpage_fetch() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"content-type": "text/html; charset=utf-8"},
            content=(
                b"<html><title>Example</title><script>x</script>"
                b"<p>Readable content.</p></html>"
            ),
        )

    client = WebpageClient(
        Settings(),
        httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    result = await client.fetch("https://example.com")
    assert result.title == "Example"
    assert result.text == "Example Readable content."
    assert result.truncated is False


@pytest.mark.asyncio
async def test_http_errors_are_safe() -> None:
    client = WebpageClient(
        Settings(),
        httpx.AsyncClient(transport=httpx.MockTransport(lambda _: httpx.Response(500))),
    )
    with pytest.raises(UpstreamError, match="HTTP 500"):
        await client.fetch("https://example.com")


@pytest.mark.asyncio
async def test_redirects_are_validated() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(302, headers={"location": "http://127.0.0.1:8080"})

    client = WebpageClient(
        Settings(),
        httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    with pytest.raises(Exception, match="Private and local"):
        await client.fetch("https://example.com")