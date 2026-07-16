import os

from google import genai
from google.genai import types

from app.agent.search import SearchResult
from app.models.classification import Classification
from app.models.service_line import ServiceLine

_client: genai.Client | None = None

EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIMENSIONS = 1536
# gemini-2.5-flash/-flash-lite are no longer available to new API keys, and
# gemini-flash-latest (the current full-tier model) returned repeated 503s
# ("experiencing high demand") when verified live. gemini-flash-lite-latest
# was confirmed reliably available, so it's used for every text call.
FLASH_MODEL = "gemini-flash-lite-latest"
FLASH_LITE_MODEL = "gemini-flash-lite-latest"


def get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    return _client


def _flatten(search_results: list[list[SearchResult]]) -> str:
    return "\n".join(f"- {r.title}: {r.snippet}" for batch in search_results for r in batch)


def embed_text(text: str, client: genai.Client | None = None) -> list[float]:
    client = client or get_client()
    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
        config=types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIMENSIONS),
    )
    return response.embeddings[0].values


def evaluate_sufficiency(search_results: list[list[SearchResult]], client: genai.Client | None = None) -> bool:
    client = client or get_client()
    response = client.models.generate_content(
        model=FLASH_LITE_MODEL,
        contents=_flatten(search_results) or "(no results yet)",
        config=types.GenerateContentConfig(
            system_instruction=(
                "You judge whether accumulated web search snippets give enough "
                "information to write a company research brief: overview, industry, "
                "size, recent news, and likely pain points. Reply with exactly one "
                "word: 'yes' or 'no'."
            ),
        ),
    )
    answer = (response.text or "").strip().lower()
    return answer.startswith("yes")


def classify(
    search_results: list[list[SearchResult]],
    service_lines: list[ServiceLine],
    client: genai.Client | None = None,
) -> Classification:
    client = client or get_client()
    lines_description = "\n".join(f"- {sl.key}: {sl.description}" for sl in service_lines)
    response = client.models.generate_content(
        model=FLASH_MODEL,
        contents=_flatten(search_results) or "(no results yet)",
        config=types.GenerateContentConfig(
            system_instruction=(
                "Classify the company described by the research notes into exactly "
                "one of these service lines, and explain why in one to two sentences.\n"
                f"{lines_description}"
            ),
            response_mime_type="application/json",
            response_schema=Classification,
        ),
    )
    if response.parsed is None:
        raise ValueError(
            "Gemini returned no parsed classification (response may have been "
            "safety-blocked or malformed)"
        )
    return response.parsed


def synthesize_brief(
    search_results: list[list[SearchResult]],
    classification: Classification,
    grounding: list[str],
    client: genai.Client | None = None,
) -> tuple[str, str]:
    client = client or get_client()
    grounding_text = "\n---\n".join(grounding) if grounding else "(no prior reference material retrieved)"
    response = client.models.generate_content(
        model=FLASH_MODEL,
        contents=(
            f"Service line classification: {classification.service_line}\n\n"
            f"Research notes:\n{_flatten(search_results)}\n\n"
            f"Reference material:\n{grounding_text}"
        ),
        config=types.GenerateContentConfig(
            system_instruction=(
                "Write a company research brief (overview, industry context, likely "
                "pain points) as one section, followed by a second section titled "
                "'Why this angle fits' that is a one-paragraph rationale for the "
                "classification below. Separate the two sections with the exact line "
                "'---'. Match the tone and phrasing of the reference material where "
                "relevant, rather than generic AI phrasing."
            ),
        ),
    )
    text = response.text or ""
    brief, _, rationale = text.partition("---")
    return brief.strip(), rationale.strip()


def generate_talking_points(
    brief: str,
    classification: Classification,
    grounding: list[str],
    client: genai.Client | None = None,
) -> list[str]:
    client = client or get_client()
    grounding_text = "\n---\n".join(grounding) if grounding else "(no prior reference material retrieved)"
    response = client.models.generate_content(
        model=FLASH_MODEL,
        contents=(
            f"Service line: {classification.service_line}\n\nBrief:\n{brief}\n\n"
            f"Reference material:\n{grounding_text}"
        ),
        config=types.GenerateContentConfig(
            system_instruction=(
                "Given the research brief and service line classification below, "
                "write 3 to 5 discovery-call talking points or questions tailored to "
                "this company and service line. Reply with one point per line, no "
                "numbering or bullets."
            ),
        ),
    )
    text = response.text or ""
    lines = [line.strip("-* ").strip() for line in text.splitlines()]
    points = [line for line in lines if line]
    if not points:
        return ["Ask about their current priorities and what's driving this conversation now."]
    return points
