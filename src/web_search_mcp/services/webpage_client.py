"""Safe async webpage fetching and readable-text extraction."""

import httpx

from web_search_mcp.config import Settings
from web_search_mcp.errors import InvalidUrlError, UpstreamError
from web_search_mcp.models import WebpageResponse
from web_search_mcp.utils.extraction import extract_readable_text
from web_search_mcp.utils.validation import validate_public_http_url


class WebpageClient:
    """Fetch public webpages without following unsafe redirects."""

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

    async def fetch(self, url: str) -> WebpageResponse:
        """Fetch a public HTML page and return readable text."""

        current_url = validate_public_http_url(url)

        for redirect_number in range(self.settings.max_redirects + 1):
            try:
                async with self._client.stream(
                    "GET",
                    current_url,
                    headers={
                        "Accept": "text/html,application/xhtml+xml",
                        "User-Agent": "web-search-mcp/0.1",
                    },
                ) as response:
                    if 300 <= response.status_code < 400:
                        location = response.headers.get("location")
                        if not location:
                            raise UpstreamError(
                                "The webpage returned an invalid redirect.",
                                "redirect_error",
                            )
                        if redirect_number >= self.settings.max_redirects:
                            raise UpstreamError(
                                "The webpage exceeded the redirect limit.",
                                "redirect_limit",
                            )
                        current_url = validate_public_http_url(
                            str(httpx.URL(current_url).join(location))
                        )
                        continue

                    if response.status_code == 404:
                        raise UpstreamError("The webpage was not found.", "not_found")
                    if response.status_code >= 400:
                        raise UpstreamError(
                            f"The webpage returned HTTP {response.status_code}.",
                            "upstream_http_error",
                        )

                    content_type = response.headers.get("content-type", "").split(";")[0].lower()
                    if content_type and content_type not in {"text/html", "application/xhtml+xml"}:
                        raise UpstreamError(
                            "The URL does not point to an HTML webpage.",
                            "unsupported_content",
                        )

                    content_length = response.headers.get("content-length")
                    if content_length and int(content_length) > self.settings.max_fetch_bytes:
                        raise UpstreamError(
                            "The webpage is too large to fetch.",
                            "response_too_large",
                        )

                    body = bytearray()
                    async for chunk in response.aiter_bytes():
                        body.extend(chunk)
                        if len(body) > self.settings.max_fetch_bytes:
                            raise UpstreamError(
                                "The webpage is too large to fetch.",
                                "response_too_large",
                            )

                    encoding = response.encoding or "utf-8"
                    html = bytes(body).decode(encoding, errors="replace")
                    text, title, truncated = extract_readable_text(
                        html,
                        max_characters=self.settings.max_response_chars,
                    )
                    return WebpageResponse(
                        url=str(response.url),
                        title=title,
                        text=text,
                        characters=len(text),
                        truncated=truncated,
                        content_type=content_type or "text/html",
                    )
            except httpx.TimeoutException as exc:
                raise UpstreamError("The webpage request timed out.", "timeout") from exc
            except httpx.RequestError as exc:
                raise UpstreamError("The webpage could not be reached.", "network_error") from exc

        raise InvalidUrlError("The webpage redirect chain was not safe.")