import os
from dataclasses import dataclass

from tavily import TavilyClient

_client: TavilyClient | None = None


def get_client() -> TavilyClient:
    global _client
    if _client is None:
        _client = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY"))
    return _client


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str


def _extract_results(response: dict) -> list[SearchResult]:
    results: list[SearchResult] = []
    for item in response.get("results", []):
        results.append(
            SearchResult(
                title=item.get("title", ""),
                url=item.get("url", ""),
                snippet=item.get("content", ""),
            )
        )
    return results


def web_search(query: str) -> list[SearchResult]:
    response = get_client().search(query=query, max_results=5)
    return _extract_results(response)
