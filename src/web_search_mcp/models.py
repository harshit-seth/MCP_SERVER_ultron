"""Structured models returned by the server's tools."""

from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    """A single web search result."""

    title: str
    url: str
    snippet: str = ""
    source: str


class SearchResponse(BaseModel):
    """The structured result of a web search."""

    query: str
    results: list[SearchResult]
    count: int


class WebpageResponse(BaseModel):
    """Readable text extracted from a webpage."""

    url: str
    title: str = ""
    text: str
    characters: int
    truncated: bool
    content_type: str = Field(default="text/html")


class ErrorDetail(BaseModel):
    """Safe error details returned from a tool."""

    code: str
    message: str


class ToolErrorResponse(BaseModel):
    """Common error envelope for MCP tools."""

    ok: bool = False
    error: ErrorDetail