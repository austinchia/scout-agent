# Scout — Agent Notes

Scout is an AI agent that takes a company/lead name and produces a research brief, service-line classification, and discovery-call talking points. v1 scope only — no deck generation, no Notion write-back (both explicitly deferred).

## Where things are documented

- **Design spec:** `docs/superpowers/specs/2026-07-15-scout-v1-design.md` — resolves the open questions from the original PRD (service line storage, RAG seeding scope, low-confidence handling) and defines the repo layout, data model, and migration approach.
- **Implementation plan:** `docs/superpowers/plans/2026-07-15-scout-v1.md` — the full task-by-task build plan (TDD steps, exact code, exact commands). Read this before touching backend code; it's the source of truth for what each file/function is supposed to do.

## Repo layout

- `backend/` — Python (uv-managed), FastAPI. `app/api` = endpoints, `app/agent` = research/classification/drafting logic, `app/models` = Pydantic schemas, `app/db` = Neon Postgres access.
- `frontend/` — React + Vite + Tailwind, added in a later phase.

## Conventions

- Python dependency management is **uv only** — `uv add`/`uv run`, not pip/poetry directly.
- Don't add a dependency outside what the plan's Global Constraints section lists without asking first.
- DB writes must be idempotent (re-running Scout on the same company updates its `profiles` row, not duplicate it).
- Checkpoint with the user after each build phase rather than running silently through the whole plan.
