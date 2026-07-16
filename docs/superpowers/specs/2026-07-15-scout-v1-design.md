# Scout v1 — Design

Layers on top of `scout-prd.md`, which remains the source of truth for product scope, data model, and agent behavior. This doc records the implementation-level decisions needed to start building, plus resolutions to the PRD's open questions (section 12).

## Scope

Exactly v1 per PRD section 11: manual trigger, single-company research, RAG-grounded brief + talking points, Neon storage. Explicitly excludes deck generation and Notion write-back (both deferred).

## Resolved open questions (PRD section 12)

1. **Known service lines location:** a Neon table (`service_lines`), not hardcoded in the prompt — editable by Austin without a redeploy as offerings evolve.
2. **`reference_docs` v0 seeding scope:** narrow — past proposal documents and service line descriptions only. Positioning notes/loose material (e.g. LinkedIn posts) are excluded from v0 to protect retrieval quality.
3. **Low-confidence briefs:** shown with a warning flag, not withheld. Austin sees the generated brief plus an explicit low-confidence label rather than nothing.
4. **Credentials:** assumed to already exist (Neon project + OpenAI API key). Setup steps produce a `.env.example` for Austin to fill in, not provisioning instructions.

## Repo layout

Single git repo, two top-level apps:

```
backend/
  pyproject.toml          # uv-managed
  app/
    main.py               # FastAPI app, mounts routes
    api/routes.py         # POST /scout/run
    agent/loop.py          # run_scout() per PRD section 6 pseudocode
    agent/search.py        # web_search wrapper (Tavily)
    agent/gemini_client.py # sufficiency/classify/synthesize/questions calls (Gemini)
    models/                # Pydantic: Classification, ScoutProfile, ServiceLine, etc.
    db/
      connection.py        # pooled Neon connection (PgBouncer-aware)
      migrations/001_init.sql
      migrate.py           # runnable migration script
      queries.py            # insert/vector_search helpers
  .env.example
frontend/
  (Vite + React + Tailwind — scaffolded last, once the API is working)
```

## Data model addition

A fourth table beyond the PRD's three (`profiles`, `reference_docs`, `scout_runs`):

**`service_lines`**
| Column | Type | Notes |
|---|---|---|
| id | uuid | primary key |
| key | text | stable identifier, e.g. `training`, `consulting`, `retainer`, `certification`, `other` |
| label | text | human-readable name |
| description | text | used both for display and as embedding source for classification grounding |
| embedding | vector | for similarity matching during classification |
| active | boolean | lets Austin retire a service line without deleting history |
| created_at | timestamp | |

Seeded at migration time with the five service lines named in PRD section 5.

## Migration

A plain Python script (`app/db/migrate.py`) using `psycopg`, invoked via `uv run python -m app.db.migrate`. It executes `001_init.sql`, which:
- enables the `pgvector` extension
- creates all four tables (`profiles`, `reference_docs`, `scout_runs`, `service_lines`)
- seeds `service_lines` with the five initial rows

Idempotent: uses `CREATE TABLE IF NOT EXISTS` and an `ON CONFLICT DO NOTHING` seed insert, so re-running is safe.

## DB connection

Uses Neon's pooled connection string (the `-pooler` host, PgBouncer in transaction mode) via `psycopg`. Each serverless invocation opens and closes its own short-lived connection — no persistent app-side connection pool, since Vercel functions are stateless between invocations.

## Build order (unchanged from user's original instructions)

1. Project scaffolding (uv, FastAPI skeleton, folder structure)
2. Pydantic models (`Classification`, `ScoutProfile`, plus `ServiceLine`)
3. Database layer (connection + migration script for all four tables)
4. Agent loop (`run_scout()`)
5. API endpoint (`POST /scout/run`)
6. Minimal frontend (React + Vite + Tailwind)

Check in with the user after each step before proceeding to the next. No package outside the PRD's tech stack (section 8) gets installed without asking first.

## Addendum (2026-07-16): model provider changed from OpenAI to Gemini + Tavily

Before Phase 4 (agent loop) was built, Austin asked to avoid OpenAI API costs. The PRD's section 8 named OpenAI specifically, so this is a deliberate deviation from the PRD, not an assumption — recorded here per the same "ask before deviating from the tech stack" rule that governs dependency choices.

**Decision:** use Google's Gemini API (free tier) for all model calls, and Tavily (free tier) for web search, instead of OpenAI. A fully local/offline model (e.g. Ollama) was considered and rejected: Vercel's serverless functions cannot reach a model running on Austin's own machine, which would break the PRD's deployed, on-demand usage model (section 6) the moment this ships past local development.

**What changes from the original plan:**
- `agent/search.py` calls the Tavily API (`tavily-python`) instead of OpenAI's Responses API hosted `web_search` tool. Tavily returns results as `{title, url, content}` directly, which is a simpler, more robust mapping to `SearchResult` than parsing OpenAI's citation-annotation format.
- `agent/openai_client.py` becomes `agent/gemini_client.py`, calling Google's `google-genai` SDK. Structured classification uses Gemini's `response_schema` + `response.parsed`, the same shape as OpenAI's `.parse()`.
- Models: `gemini-2.5-flash-lite` for the sufficiency check (cheapest/fastest, matches the PRD's original intent of a lighter model for that step), `gemini-2.5-flash` for classification/synthesis/talking points, `gemini-embedding-001` for embeddings.
- **No change to the already-built database schema:** Gemini's embedding model supports configurable output dimensionality (768/1536/3072 via Matryoshka Representation Learning). Setting `output_dimensionality=1536` keeps embeddings compatible with the `VECTOR(1536)` columns Task 4 already migrated — no schema rework needed.
- New env vars: `GEMINI_API_KEY`, `TAVILY_API_KEY` (replacing `OPENAI_API_KEY`). New dependencies: `google-genai`, `tavily-python` (replacing `openai`, which Task 1 had added and is now removed).
- Cost profile: both providers' free tiers are rate-limited (requests per minute/day), not unlimited — acceptable for Scout's low-frequency, on-demand usage pattern (PRD section 8's own reasoning for choosing Neon's scale-to-zero pricing applies here too).
