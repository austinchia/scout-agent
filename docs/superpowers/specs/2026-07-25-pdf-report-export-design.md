# PDF Report Export — Design

Adds a "Download PDF" button to the existing Scout frontend (`frontend/src/App.tsx`) that lets Austin export a generated `ScoutProfile` as a PDF once results are on screen. No backend changes.

## Scope

Client-side export of the already-rendered report only. Explicitly out of scope: deck generation and Notion write-back (both deferred per `2026-07-15-scout-v1-design.md`), any backend endpoint, any new UI state beyond the button itself, multiple export formats (PDF only for now).

## Architecture & components

- New frontend dependency: `pdfmake`. Chosen over `jsPDF` because it lays out and wraps multi-line body text (the `brief` and `rationale` fields can run long) without manual line-splitting.
- New file `frontend/src/lib/exportReport.ts`, exporting one function:
  ```ts
  function downloadScoutReportPdf(profile: ScoutProfile, companyName: string): void
  ```
  It builds a pdfmake document definition from the profile and triggers the browser download (`pdfMake.createPdf(docDefinition).download(filename)`). Keeping this out of `App.tsx` keeps the component focused on fetch/render, and makes the export logic something that can be read and changed independently of the form/results UI.
- `App.tsx` changes: one button rendered inside the existing `{profile && (...)}` block, calling `downloadScoutReportPdf(profile, companyName)` on click. No new React state — this is a synchronous, one-shot action triggered from data already in memory, not a request that needs loading/error state.

## Data flow

1. User runs a scout query; `profile` state populates as it does today.
2. User clicks "Download PDF".
3. `downloadScoutReportPdf` reads `profile` (already in scope via closure) and `companyName`, builds the pdfmake doc definition, and calls `.download()`.
4. Browser saves the file. No server round-trip, no loading state.

## PDF content

- **Filename:** `<slugified-company-name>-scout-report-<YYYY-MM-DD>.pdf` (slugify: lowercase, spaces/non-alphanumerics to hyphens).
- **Header:** company name as title, "Generated <YYYY-MM-DD>" as subtitle.
- **Low-confidence note:** if `profile.low_confidence` is true, an amber-styled callout line directly under the header, using the same wording as the on-screen warning ("Low confidence: limited public information was found for this company. Treat this brief as a starting point, not a finished picture.").
- **Body sections, in this order** (matching on-screen order):
  1. Classification — service line + confidence percentage (e.g. "Training (82% confidence)")
  2. Brief
  3. Why this angle fits (`rationale`)
  4. Talking points — rendered as a bulleted list
- Styling is simple heading/body text hierarchy (bold section headers, regular body text) — no requirement to pixel-match the on-screen Tailwind styling.

## Error handling

None needed beyond what already exists: the button only renders once `profile` is non-null, so there's no null/loading state to guard against, and PDF generation is synchronous/local — no network call that can fail.

## Testing

No test framework exists in `frontend/` (noted in the pending shadcn-redesign plan; out of scope to add one here). Verification is:
- `pnpm run build` (`tsc -b && vite build`) and `pnpm lint` (oxlint) pass.
- Manual check via `pnpm dev`: run a query, click "Download PDF", confirm the file downloads with the correct filename and the PDF content matches the profile shown on screen (including the low-confidence case).
