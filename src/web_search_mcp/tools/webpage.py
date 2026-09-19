"""Webpage fetching tool logic."""

from web_search_mcp.models import WebpageResponse
from web_search_mcp.services.webpage_client import WebpageClient


async def fetch_webpage(client: WebpageClient, url: str) -> WebpageResponse:
    """Fetch and extract readable text from a public webpage."""

    return await client.fetch(url)