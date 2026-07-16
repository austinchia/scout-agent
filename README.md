# scout-agent

Scout is an AI agent that takes a company/lead name and produces a research brief, service-line classification, and discovery-call talking points. It's manually triggered, single-company per run, and grounds its output in a Neon/pgvector-backed set of reference docs (past proposals, service line descriptions).

v1 scope only — deck generation and Notion write-back are explicitly deferred.

## How it works

1. `POST /scout/run` with a `company_name` (and optional `note`).
2. The agent loop (`app/agent/loop.py`) runs a sufficiency check, web search (Tavily), service-line classification, and brief/talking-points synthesis (Gemini), grounded against `reference_docs` and `service_lines` via vector similarity.
3. The result — a `ScoutProfile` (classification, brief, talking points, rationale, low-confidence flag) — is persisted to Neon and returned to the frontend.

Low-confidence briefs are still shown, with a warning flag, rather than withheld.

## Tech stack

- **Backend:** Python 3.11, FastAPI, [uv](https://docs.astral.sh/uv/) for dependency management
- **Model/search:** Gemini (`gemini-2.5-flash-lite` / `gemini-2.5-flash` / `gemini-embedding-001`) via `google-genai`, Tavily for web search
- **Database:** Neon Postgres + `pgvector`, accessed via `psycopg`
- **Frontend:** React + Vite + Tailwind (pnpm)
- **Deployment:** Vercel (`vercel.json` services config — see below)

## Repo layout

```
backend/
  pyproject.toml          # uv-managed
  app/
    main.py               # FastAPI app, mounts routes
    api/routes.py          # POST /scout/run
    agent/loop.py          # run_scout()
    agent/search.py        # Tavily web search wrapper
    agent/gemini_client.py # sufficiency/classify/synthesize/questions calls
    models/                # Pydantic: Classification, ScoutProfile, ServiceLine
    db/                    # Neon connection, migrations, queries
  .env.example
frontend/                 # Vite + React + Tailwind
```

## Getting started

### Backend

```bash
cd backend
cp .env.example .env   # fill in DATABASE_URL, GEMINI_API_KEY, TAVILY_API_KEY
uv sync
uv run python -m app.db.migrate   # idempotent: creates tables, seeds service_lines
uv run uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
pnpm install
pnpm dev
```

## Deployment

Deployed to Vercel as two services defined in `vercel.json`: the FastAPI backend (`backend/`, via `app.main:app`) and the Vite frontend (`frontend/`), routed by path (`/scout/*`, `/health` → backend; everything else → frontend). Backend secrets (`DATABASE_URL`, `GEMINI_API_KEY`, `TAVILY_API_KEY`) must also be set as Vercel environment variables — a local `.env` only covers local development.

## Docs

- **Design spec:** `docs/superpowers/specs/2026-07-15-scout-v1-design.md` — repo layout, data model additions, provider choice (Gemini + Tavily over OpenAI)
- **Implementation plan:** `docs/superpowers/plans/2026-07-15-scout-v1.md` — task-by-task build plan
- **Agent notes:** `AGENTS.md` — conventions for anyone (human or agent) working on this repo
