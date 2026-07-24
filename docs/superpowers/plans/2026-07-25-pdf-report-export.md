# PDF Report Export Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a "Download PDF" button to the Scout frontend that exports the on-screen `ScoutProfile` result as a PDF, generated entirely client-side.

**Architecture:** A new pure-function module (`frontend/src/lib/exportReport.ts`) builds a `pdfmake` document definition from the existing `ScoutProfile` data and triggers a browser download. `App.tsx` gets one new button that calls this function with data already sitting in its React state — no new state, no backend changes.

**Tech Stack:** `pdfmake@0.2.23` (client-side PDF generation) + `@types/pdfmake@0.2.13` (dev-only type definitions), added to the existing Vite + React 19 + TypeScript + Tailwind v4 frontend (pnpm-managed).

## Global Constraints

- Client-side only — no backend endpoint, no new Python dependency (per `docs/superpowers/specs/2026-07-25-pdf-report-export-design.md`).
- PDF is the only export format for now.
- Pin exact versions: `pdfmake@0.2.23`, `@types/pdfmake@0.2.13`. These were verified directly (package contents + type declarations inspected) — do not let a package manager resolve to a newer major (0.3.x is a breaking rewrite with a different, less-bundler-friendly API).
- Filename format: `<slugified-company-name>-scout-report-<YYYY-MM-DD>.pdf`.
- PDF body section order: Classification → Brief → Why this angle fits → Talking points, matching the on-screen order. Low-confidence note (if applicable) appears directly under the header.
- No test framework exists in `frontend/` and none is added by this plan. Verification per task is `pnpm run build` (`tsc -b && vite build`), `pnpm lint` (oxlint), and — for the final task — a manual check via `pnpm dev`.
- `frontend/tsconfig.app.json` currently has no `esModuleInterop` setting (defaults to `false`). It must be set to `true` for `pdfmake/build/vfs_fonts` (a CJS `export =` module) to be importable as a default import. This was confirmed by reading `node_modules/@types/pdfmake/build/vfs_fonts.d.ts` (`declare const vfs: {...}; export = vfs;`) and `node_modules/@types/pdfmake/build/pdfmake.d.ts` (which uses plain named exports, so it needs no interop flag).

---

### Task 1: Add pdfmake dependencies and enable esModuleInterop

**Files:**
- Modify: `frontend/package.json` (via `pnpm add`, not hand-edited)
- Modify: `frontend/tsconfig.app.json`

**Interfaces:**
- Produces: `pdfmake` and `@types/pdfmake` available to import from anywhere under `frontend/src/`; `esModuleInterop: true` active for the whole `frontend/` TypeScript project.

- [ ] **Step 1: Install pdfmake and its types at pinned versions**

Run:
```bash
cd frontend
pnpm add pdfmake@0.2.23
pnpm add -D @types/pdfmake@0.2.13
```

Expected: `frontend/package.json` gains `"pdfmake": "0.2.23"` under `dependencies` and `"@types/pdfmake": "0.2.13"` under `devDependencies`; `frontend/pnpm-lock.yaml` updates.

- [ ] **Step 2: Enable esModuleInterop in tsconfig.app.json**

Open `frontend/tsconfig.app.json` and add `"esModuleInterop": true` inside `compilerOptions`, alongside the existing `"moduleResolution": "bundler"` block:

```json
    /* Bundler mode */
    "moduleResolution": "bundler",
    "esModuleInterop": true,
    "allowImportingTsExtensions": true,
```

- [ ] **Step 3: Verify the project still builds**

Run: `cd frontend && pnpm run build`
Expected: succeeds with no new errors (no code references pdfmake yet, so this just confirms the dependency install and tsconfig change didn't break anything).

- [ ] **Step 4: Commit**

```bash
git add frontend/package.json frontend/pnpm-lock.yaml frontend/tsconfig.app.json
git commit -m "Add pdfmake dependency for client-side PDF export"
```

---

### Task 2: Export ScoutProfile types and add the PDF-building module

**Files:**
- Modify: `frontend/src/App.tsx:3-16` (add `export` to the two existing type declarations)
- Create: `frontend/src/lib/exportReport.ts`

**Interfaces:**
- Consumes: `pdfmake/build/pdfmake` (`createPdf`), `pdfmake/build/vfs_fonts` (default export: the font virtual-file-system map), `pdfmake/interfaces` (`TDocumentDefinitions` type).
- Produces: `export type Classification` and `export type ScoutProfile` from `App.tsx` (previously unexported). `export function downloadScoutReportPdf(profile: ScoutProfile, companyName: string): void` from `frontend/src/lib/exportReport.ts` — this is what Task 3 imports and calls.

- [ ] **Step 1: Export the existing types from App.tsx**

In `frontend/src/App.tsx`, change:

```ts
type Classification = {
  service_line: string
  confidence: number
  rationale: string
}

type ScoutProfile = {
```

to:

```ts
export type Classification = {
  service_line: string
  confidence: number
  rationale: string
}

export type ScoutProfile = {
```

(Only the two `type` keywords gain `export` — no other changes to the type bodies.)

- [ ] **Step 2: Write the PDF-building module**

Create `frontend/src/lib/exportReport.ts`:

```ts
import { createPdf } from 'pdfmake/build/pdfmake'
import pdfFonts from 'pdfmake/build/vfs_fonts'
import type { TDocumentDefinitions } from 'pdfmake/interfaces'
import type { ScoutProfile } from '../App'

function slugify(value: string): string {
  return value
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/(^-+)|(-+$)/g, '')
}

function todayIsoDate(): string {
  return new Date().toISOString().slice(0, 10)
}

const LOW_CONFIDENCE_NOTE =
  'Low confidence: limited public information was found for this company. Treat this brief as a starting point, not a finished picture.'

export function downloadScoutReportPdf(profile: ScoutProfile, companyName: string): void {
  const date = todayIsoDate()
  const filename = `${slugify(companyName)}-scout-report-${date}.pdf`

  const docDefinition: TDocumentDefinitions = {
    defaultStyle: { font: 'Roboto', fontSize: 11 },
    content: [
      { text: companyName, style: 'title' },
      { text: `Generated ${date}`, style: 'subtitle' },
      ...(profile.low_confidence
        ? [{ text: LOW_CONFIDENCE_NOTE, style: 'warning' }]
        : []),
      { text: 'Classification', style: 'sectionHeader' },
      {
        text: `${profile.classification.service_line} (${Math.round(profile.classification.confidence * 100)}% confidence)`,
        margin: [0, 0, 0, 12] as [number, number, number, number],
      },
      { text: 'Brief', style: 'sectionHeader' },
      { text: profile.brief, margin: [0, 0, 0, 12] as [number, number, number, number] },
      { text: 'Why this angle fits', style: 'sectionHeader' },
      { text: profile.rationale, margin: [0, 0, 0, 12] as [number, number, number, number] },
      { text: 'Talking points', style: 'sectionHeader' },
      { ul: profile.talking_points, margin: [0, 0, 0, 12] as [number, number, number, number] },
    ],
    styles: {
      title: { fontSize: 20, bold: true, margin: [0, 0, 0, 4] },
      subtitle: { fontSize: 10, color: '#666666', margin: [0, 0, 0, 12] },
      warning: { fontSize: 10, color: '#92400e', margin: [0, 0, 0, 16] },
      sectionHeader: { fontSize: 13, bold: true, margin: [0, 8, 0, 4] },
    },
  }

  createPdf(docDefinition, undefined, undefined, pdfFonts).download(filename)
}
```

- [ ] **Step 3: Verify the project builds and lints**

Run: `cd frontend && pnpm run build && pnpm lint`
Expected: both succeed. If `tsc` complains about the `pdfmake/interfaces` or `pdfmake/build/pdfmake` import paths, re-check that Task 1's `esModuleInterop` change landed and that `@types/pdfmake@0.2.13` installed (its subpath `.d.ts` files are what make these imports resolve).

- [ ] **Step 4: Commit**

```bash
git add frontend/src/App.tsx frontend/src/lib/exportReport.ts
git commit -m "Add downloadScoutReportPdf for client-side report export"
```

---

### Task 3: Wire the Download PDF button into the results view

**Files:**
- Modify: `frontend/src/App.tsx:100-101` (top of the `{profile && (...)}` block)

**Interfaces:**
- Consumes: `downloadScoutReportPdf(profile: ScoutProfile, companyName: string): void` from `frontend/src/lib/exportReport.ts` (Task 2). `companyName` and `profile` are both already-existing state in `App.tsx`.

- [ ] **Step 1: Import the export function**

At the top of `frontend/src/App.tsx`, add alongside the existing `useState` import:

```ts
import { downloadScoutReportPdf } from './lib/exportReport'
```

- [ ] **Step 2: Add the button at the top of the results block**

In `frontend/src/App.tsx`, change:

```tsx
        {profile && (
          <div className="mt-8 space-y-6">
            {profile.low_confidence && (
```

to:

```tsx
        {profile && (
          <div className="mt-8 space-y-6">
            <div className="flex justify-end">
              <button
                type="button"
                onClick={() => downloadScoutReportPdf(profile, companyName)}
                className="rounded-md border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-100"
              >
                Download PDF
              </button>
            </div>
            {profile.low_confidence && (
```

- [ ] **Step 3: Verify the project builds and lints**

Run: `cd frontend && pnpm run build && pnpm lint`
Expected: both succeed with no errors.

- [ ] **Step 4: Manual verification**

Run: `cd frontend && pnpm dev`, open the printed local URL, submit a company name, wait for results, click "Download PDF".
Expected:
- A file named `<slugified-company-name>-scout-report-<today's-date>.pdf` downloads.
- Opening it shows: company name + generated date at the top, the low-confidence note if `profile.low_confidence` was true, then Classification, Brief, Why this angle fits, and Talking points (as a bulleted list), in that order, matching what's on screen.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/App.tsx
git commit -m "Add Download PDF button to Scout results view"
```
