"""Web search tool logic."""

from web_search_mcp.models import SearchResponse
from web_search_mcp.services.search_client import SearchClient
from web_search_mcp.utils.validation import validate_max_results, validate_query


async def web_search(
    client: SearchClient,
    query: str,
    max_results: int = 5,
) -> SearchResponse:
    """Validate a query and search the configured provider."""

    normalized_query = validate_query(query)
    validated_max_results = validate_max_results(max_results)
    return await client.search(normalized_query, validated_max_results)