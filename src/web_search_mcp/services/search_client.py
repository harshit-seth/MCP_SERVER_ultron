"""Async client for a Brave-compatible web search API."""

from urllib.parse import urlparse

import httpx

from web_search_mcp.config import Settings
from web_search_mcp.errors import ConfigurationError, UpstreamError
from web_search_mcp.models import SearchResponse, SearchResult


class SearchClient:
    """Call a configured search API and normalize its response."""

    def __init__(
        self,
        settings: Settings,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.settings = settings
        self._client = client or httpx.AsyncClient(
            timeout=settings.request_timeout_seconds,
            follow_redirects=False,
        )
        self._owns_client = client is None

    async def close(self) -> None:
        """Close the underlying HTTP client when this instance owns it."""

        if self._owns_client:
            await self._client.aclose()

    async def search(self, query: str, max_results: int) -> SearchResponse:
        """Search the configured provider and return normalized results."""

        if not self.settings.search_api_key:
            raise ConfigurationError(
                "Search is not configured. Set SEARCH_API_KEY in the environment."
            )

        try:
            response = await self._client.get(
                self.settings.search_endpoint,
                params={"q": query, "count": max_results},
                headers={
                    "Accept": "application/json",
                    "X-Subscription-Token": self.settings.search_api_key,
                },
            )
        except httpx.TimeoutException as exc:
            raise UpstreamError("The search provider timed out.", "timeout") from exc
        except httpx.RequestError as exc:
            raise UpstreamError(
                "The search provider could not be reached.",
                "network_error",
            ) from exc

        if response.status_code == 401 or response.status_code == 403:
            raise UpstreamError(
                "The search provider rejected the configured credentials.",
                "auth_error",
            )
        if response.status_code == 429:
            raise UpstreamError("The search provider rate limit was reached.", "rate_limited")
        if response.is_error:
            raise UpstreamError(
                f"The search provider returned HTTP {response.status_code}.",
                "upstream_http_error",
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise UpstreamError(
                "The search provider returned malformed JSON.",
                "invalid_response",
            ) from exc

        raw_results = payload.get("web", {}).get("results") if isinstance(payload, dict) else None
        if raw_results is None and isinstance(payload, dict):
            raw_results = payload.get("results")
        if not isinstance(raw_results, list):
            raise UpstreamError(
                "The search provider returned an unexpected response.",
                "invalid_response",
            )

        results: list[SearchResult] = []
        for item in raw_results:
            if not isinstance(item, dict):
                continue
            title = item.get("title")
            url = item.get("url") or item.get("link")
            snippet = item.get("description") or item.get("snippet") or ""
            if not isinstance(title, str) or not isinstance(url, str):
                continue
            if not url.startswith(("http://", "https://")):
                continue
            hostname = urlparse(url).hostname or ""
            results.append(
                SearchResult(
                    title=title.strip(),
                    url=url,
                    snippet=str(snippet).strip(),
                    source=hostname,
                )
            )
            if len(results) >= max_results:
                break

        return SearchResponse(query=query, results=results, count=len(results))