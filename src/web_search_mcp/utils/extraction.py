"""HTML-to-text extraction helpers."""

import re

from bs4 import BeautifulSoup


def extract_readable_text(
    html: str,
    *,
    max_characters: int,
) -> tuple[str, str, bool]:
    """Extract page title and readable text while enforcing a size limit."""

    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else ""

    for element in soup(
        ["script", "style", "noscript", "template", "svg", "canvas", "iframe"]
    ):
        element.decompose()

    text = soup.get_text(" ", strip=True)
    text = re.sub(r"\s+", " ", text).strip()
    truncated = len(text) > max_characters
    return text[:max_characters], title[:500], truncated