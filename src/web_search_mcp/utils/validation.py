"""Input and SSRF protection validation."""

import ipaddress
import socket
from urllib.parse import urlparse

from web_search_mcp.errors import InvalidInputError, InvalidUrlError


def validate_query(query: str) -> str:
    """Normalize and validate a natural-language search query."""

    if not isinstance(query, str):
        raise InvalidInputError("query must be a string.")

    normalized = " ".join(query.split())
    if not normalized:
        raise InvalidInputError("query must not be empty.")
    if len(normalized) > 500:
        raise InvalidInputError("query must be 500 characters or fewer.")
    return normalized


def validate_max_results(max_results: int) -> int:
    """Validate the requested number of search results."""

    if isinstance(max_results, bool) or not isinstance(max_results, int):
        raise InvalidInputError("max_results must be an integer between 1 and 10.")
    if not 1 <= max_results <= 10:
        raise InvalidInputError("max_results must be between 1 and 10.")
    return max_results


def _is_private_ip(value: str) -> bool:
    """Return whether an address belongs to a non-public network."""

    address = ipaddress.ip_address(value)
    return any(
        (
            address.is_private,
            address.is_loopback,
            address.is_link_local,
            address.is_multicast,
            address.is_reserved,
            address.is_unspecified,
        )
    )


def _resolved_addresses(hostname: str) -> set[str]:
    """Resolve a hostname and return every address it resolves to."""

    try:
        return {
            item[4][0]
            for item in socket.getaddrinfo(
                hostname,
                None,
                type=socket.SOCK_STREAM,
            )
        }
    except socket.gaierror as exc:
        raise InvalidUrlError("The hostname could not be resolved.") from exc


def validate_public_http_url(url: str) -> str:
    """Validate an HTTP(S) URL and reject local/private network targets."""

    if not isinstance(url, str) or len(url) > 2_048:
        raise InvalidUrlError("url must be a valid HTTP or HTTPS URL.")

    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise InvalidUrlError("Only HTTP and HTTPS URLs are supported.")
    if parsed.username or parsed.password:
        raise InvalidUrlError("URLs containing credentials are not supported.")

    hostname = parsed.hostname.rstrip(".").lower()
    if hostname in {"localhost", "localhost.localdomain"} or hostname.endswith(".local"):
        raise InvalidUrlError("Local network URLs are not allowed.")

    try:
        addresses = {_ for _ in [hostname] if ":" in _ or _.replace(".", "").isdigit()}
        if not addresses:
            addresses = _resolved_addresses(hostname)
        if any(_is_private_ip(address) for address in addresses):
            raise InvalidUrlError("Private and local network URLs are not allowed.")
    except ValueError as exc:
        raise InvalidUrlError("The URL contains an invalid hostname.") from exc

    return url