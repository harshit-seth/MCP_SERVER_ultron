"""Validation tests."""

import pytest

from web_search_mcp.errors import InvalidInputError, InvalidUrlError
from web_search_mcp.utils.validation import (
    validate_max_results,
    validate_public_http_url,
    validate_query,
)


def test_query_is_normalized() -> None:
    assert validate_query("  python   mcp  ") == "python mcp"


def test_empty_query_is_rejected() -> None:
    with pytest.raises(InvalidInputError, match="must not be empty"):
        validate_query("  ")


@pytest.mark.parametrize("value", [0, 11, True, "5"])
def test_invalid_result_limits_are_rejected(value: object) -> None:
    with pytest.raises(InvalidInputError):
        validate_max_results(value)  # type: ignore[arg-type]


def test_public_https_url_is_allowed() -> None:
    assert validate_public_http_url("https://example.com/docs") == "https://example.com/docs"


@pytest.mark.parametrize(
    "url",
    ["ftp://example.com", "http://localhost:8080", "http://127.0.0.1:8000", "https://foo.local"],
)
def test_private_or_invalid_urls_are_rejected(url: str) -> None:
    with pytest.raises(InvalidUrlError):
        validate_public_http_url(url)