from app.agent.search import SearchResult, _extract_results


def _fake_response():
    return {
        "query": "Groupe Clarins",
        "results": [
            {
                "title": "Clarins overview",
                "url": "https://example.com/clarins",
                "content": "Clarins is a cosmetics company.",
            },
            {
                "title": "Clarins news",
                "url": "https://example.com/clarins-news",
                "content": "Recent Clarins announcement.",
            },
        ],
    }


def test_extract_results_parses_search_results():
    results = _extract_results(_fake_response())
    assert results == [
        SearchResult(title="Clarins overview", url="https://example.com/clarins", snippet="Clarins is a cosmetics company."),
        SearchResult(title="Clarins news", url="https://example.com/clarins-news", snippet="Recent Clarins announcement."),
    ]


def test_extract_results_returns_empty_list_for_no_results():
    assert _extract_results({"results": []}) == []


def test_extract_results_handles_missing_fields_gracefully():
    response = {"results": [{"url": "https://example.com/x"}]}
    results = _extract_results(response)
    assert results == [SearchResult(title="", url="https://example.com/x", snippet="")]
