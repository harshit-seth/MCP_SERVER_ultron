"""Search client tests with mocked upstream requests."""

import httpx
import pytest

from web_search_mcp.config import Settings
from web_search_mcp.errors import ConfigurationError, UpstreamError
from web_search_mcp.services.search_client import SearchClient
from web_search_mcp.tools.search import web_search


def settings() -> Settings:
    return Settings(search_api_key="test-key")


@pytest.mark.asyncio
async def test_successful_search_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["q"] == "python mcp"
        assert request.url.params["count"] == "2"
        assert request.headers["x-subscription-token"] == "test-key"
        return httpx.Response(
            200,
            json={
                "web": {
                    "results": [
                        {
                            "title": "MCP Python SDK",
                            "url": "https://example.com/mcp",
                            "description": "Build MCP servers in Python.",
                        }
                    ]
                }
            },
        )

    client = SearchClient(settings(), httpx.AsyncClient(transport=httpx.MockTransport(handler)))
    result = await web_search(client, "python mcp", 2)
    assert result.count == 1
    assert result.results[0].source == "example.com"


@pytest.mark.asyncio
async def test_missing_search_configuration_is_clear() -> None:
    client = SearchClient(
        Settings(),
        httpx.AsyncClient(
            transport=httpx.MockTransport(lambda _: httpx.Response(200)),
        ),
    )
    with pytest.raises(ConfigurationError, match="SEARCH_API_KEY"):
        await client.search("anything", 5)


@pytest.mark.asyncio
async def test_search_api_failure_is_safe() -> None:
    transport = httpx.MockTransport(lambda _: httpx.Response(429))
    client = SearchClient(settings(), httpx.AsyncClient(transport=transport))
    with pytest.raises(UpstreamError, match="rate limit"):
        await client.search("anything", 5)


@pytest.mark.asyncio
async def test_search_timeout_is_safe() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out")

    client = SearchClient(settings(), httpx.AsyncClient(transport=httpx.MockTransport(handler)))
    with pytest.raises(UpstreamError, match="timed out"):
        await client.search("anything", 5)