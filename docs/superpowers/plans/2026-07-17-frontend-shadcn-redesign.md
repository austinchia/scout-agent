# Frontend shadcn Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restyle the existing Scout frontend (`frontend/src/App.tsx`) with shadcn/ui components: a dark-only, mobile-friendly, "internal ops tool" look, with no changes to backend behavior or data flow.

**Architecture:** Single-page React app, single component (`App.tsx`). No routing, no state library — shadcn/ui components are added as owned source files via the CLI and composed directly into the existing form → results flow.

**Tech Stack:** Vite 8, React 19, Tailwind CSS v4, shadcn/ui CLI (Radix primitives, `class-variance-authority`, `tailwind-merge`, `lucide-react`), pnpm.

## Global Constraints

- Theme is dark-only — no light mode, no `next-themes`, no toggle UI.
- Accent/primary color is the existing brand purple from `frontend/public/favicon.svg`: `#863bff` (primary), with a near-white foreground for contrast on it.
- Use the official `shadcn` CLI to scaffold components — do not hand-write shadcn-style components.
- Path alias `@/*` → `frontend/src/*`, set up by the CLI.
- Components used: `button`, `input`, `label`, `card`, `tabs`, `badge`, `alert`, `skeleton`, `separator`.
- `TabsList` must be `grid grid-cols-3 w-full` (equal-width touch targets), not the shadcn default inline-flex.
- Submit button is `w-full` on mobile, auto-width from `sm:` breakpoint up.
- Content column stays `max-w-2xl` with `px-4` at every breakpoint.
- No test framework exists in `frontend/` (no vitest, no RTL) — verification per task is `pnpm run build` (runs `tsc -b && vite build`) and `pnpm lint` (oxlint), plus a manual visual check via `pnpm dev`. Do not add a test framework as part of this plan — out of scope.
- Delete unused Vite-boilerplate files: `frontend/src/App.css`, `frontend/src/assets/react.svg`, `frontend/src/assets/vite.svg`, `frontend/src/assets/hero.png`.

---

### Task 1: Initialize shadcn/ui and install required primitives

**Files:**
- Create: `frontend/components.json`
- Create: `frontend/src/lib/utils.ts`
- Create: `frontend/src/components/ui/button.tsx`
- Create: `frontend/src/components/ui/input.tsx`
- Create: `frontend/src/components/ui/label.tsx`
- Create: `frontend/src/components/ui/card.tsx`
- Create: `frontend/src/components/ui/tabs.tsx`
- Create: `frontend/src/components/ui/badge.tsx`
- Create: `frontend/src/components/ui/alert.tsx`
- Create: `frontend/src/components/ui/skeleton.tsx`
- Create: `frontend/src/components/ui/separator.tsx`
- Modify: `frontend/package.json` (new deps, added by the CLI)
- Modify: `frontend/vite.config.ts` (`@` alias, added by the CLI)
- Modify: `frontend/tsconfig.json`, `frontend/tsconfig.app.json` (`paths`, added by the CLI)
- Modify: `frontend/src/index.css` (theme tokens, added by the CLI)

**Interfaces:**
- Produces: `@/lib/utils` exporting `cn(...inputs: ClassValue[]): string`; `@/components/ui/{button,input,label,card,tabs,badge,alert,skeleton,separator}` exporting the standard shadcn component sets (e.g. `Button`, `Card`/`CardHeader`/`CardTitle`/`CardDescription`/`CardContent`, `Tabs`/`TabsList`/`TabsTrigger`/`TabsContent`, `Badge`, `Alert`/`AlertTitle`/`AlertDescription`, `Skeleton`).

- [ ] **Step 1: Install existing dependencies**

Run: `cd frontend && pnpm install`
Expected: completes without error, creates `frontend/node_modules`.

- [ ] **Step 2: Verify the project builds before making changes**

Run: `pnpm run build` (from `frontend/`)
Expected: PASS — `tsc -b && vite build` completes with no errors, `dist/` is produced.

- [ ] **Step 3: Run the shadcn CLI init (non-interactive)**

Run: `npx shadcn@latest init -d` (from `frontend/`)
Expected: creates `components.json` and `src/lib/utils.ts`, adds `class-variance-authority`, `clsx`, `tailwind-merge`, `lucide-react` (and `tw-animate-css` if the generated CSS uses it) to `package.json`, and adds a `@` → `./src` path alias to `vite.config.ts`, `tsconfig.json`, and `tsconfig.app.json`.

- [ ] **Step 4: Add the required component primitives**

Run: `npx shadcn@latest add button input label card tabs badge alert skeleton separator` (from `frontend/`)
Expected: creates one file per component under `frontend/src/components/ui/`, no overwrite prompts (fresh install).

- [ ] **Step 5: Verify the project still builds**

Run: `pnpm run build` (from `frontend/`)
Expected: PASS — no TypeScript or build errors. `App.tsx` is untouched at this point, so behavior is unchanged; only new files and config exist.

- [ ] **Step 6: Commit**

```bash
git add frontend/components.json frontend/src/lib frontend/src/components frontend/package.json frontend/pnpm-lock.yaml frontend/vite.config.ts frontend/tsconfig.json frontend/tsconfig.app.json frontend/src/index.css
git commit -m "Add shadcn/ui CLI setup and base component primitives"
```

---

### Task 2: Configure dark-only theme with brand accent color

**Files:**
- Modify: `frontend/index.html`
- Modify: `frontend/src/index.css`

**Interfaces:**
- Consumes: the `:root` / `.dark` CSS custom-property blocks and `@theme inline` mapping generated by Task 1's `shadcn init`.
- Produces: a page that renders in dark mode by default, with `--primary` / `--primary-foreground` / `--ring` set to the brand purple.

- [ ] **Step 1: Force dark mode on**

In `frontend/index.html`, change:

```html
<html lang="en">
```

to:

```html
<html lang="en" class="dark">
```

- [ ] **Step 2: Set the brand accent color**

Open `frontend/src/index.css`. The CLI generates a `.dark { ... }` block of CSS custom properties (alongside a `:root { ... }` block for light mode, which stays unused since `.dark` is always applied). Inside the `.dark` block, set these three properties — add them if the generated block doesn't already declare them, otherwise overwrite the generated values:

```css
--primary: #863bff;
--primary-foreground: #f5f0ff;
--ring: #863bff;
```

- [ ] **Step 3: Verify the build still passes**

Run: `pnpm run build` (from `frontend/`)
Expected: PASS — CSS changes don't affect TypeScript/build correctness.

- [ ] **Step 4: Manual visual check**

Run: `pnpm dev` (from `frontend/`), open the printed local URL in a browser.
Expected (manual observation): the page background is dark, and is otherwise unchanged from before (App.tsx hasn't been touched yet) except for the dark background color. Stop the dev server after checking.

- [ ] **Step 5: Commit**

```bash
git add frontend/index.html frontend/src/index.css
git commit -m "Force dark theme and set brand purple as the primary accent color"
```

---

### Task 3: Rebuild the page shell and form with shadcn primitives

**Files:**
- Modify: `frontend/src/App.tsx`

**Interfaces:**
- Consumes: `Button` from `@/components/ui/button`, `Input` from `@/components/ui/input`, `Label` from `@/components/ui/label`, `Card`/`CardHeader`/`CardTitle`/`CardDescription`/`CardContent` from `@/components/ui/card`, `Loader2` from `lucide-react` (all produced by Task 1).
- Produces: the full-page shell (top bar + centered column) and the form section, which Task 4 renders results below.

- [ ] **Step 1: Replace `App.tsx` with the shell + form version**

Replace the full contents of `frontend/src/App.tsx` with:

```tsx
import { useState } from 'react'
import { Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'

type Classification = {
  service_line: string
  confidence: number
  rationale: string
}

type ScoutProfile = {
  id: string | null
  company_name: string
  note: string | null
  classification: Classification
  brief: string
  talking_points: string[]
  rationale: string
  reference_doc_ids: string[]
  low_confidence: boolean
}

export default function App() {
  const [companyName, setCompanyName] = useState('')
  const [note, setNote] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [profile, setProfile] = useState<ScoutProfile | null>(null)

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    setLoading(true)
    setError(null)
    setProfile(null)
    try {
      const response = await fetch('/scout/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ company_name: companyName, note: note || null }),
      })
      if (!response.ok) {
        const body = await response.json().catch(() => null)
        throw new Error(body?.detail ?? `Request failed with status ${response.status}`)
      }
      setProfile(await response.json())
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border px-4 py-3 sm:px-6">
        <div className="mx-auto flex max-w-2xl items-center gap-2">
          <img src="/favicon.svg" alt="" className="h-6 w-6" />
          <span className="text-sm font-semibold tracking-tight text-foreground">Scout</span>
        </div>
      </header>

      <main className="mx-auto max-w-2xl px-4 py-6 sm:py-10">
        <Card>
          <CardHeader>
            <CardTitle>Research a company</CardTitle>
            <CardDescription>
              Paste a company name to generate a research brief and discovery-call talking points.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="company_name">Company name</Label>
                <Input
                  id="company_name"
                  required
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  placeholder="Enter a company name"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="note">Note (optional)</Label>
                <Input
                  id="note"
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  placeholder="Inbound via HR contact, interested in Power BI training"
                />
              </div>
              <Button type="submit" disabled={loading} className="w-full sm:w-auto">
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Researching…
                  </>
                ) : (
                  'Run Scout'
                )}
              </Button>
            </form>
          </CardContent>
        </Card>
      </main>
    </div>
  )
}
```

Note: this intentionally drops the old error/results JSX for now — Task 4 adds it back using shadcn components.

- [ ] **Step 2: Verify build and lint pass**

Run: `pnpm run build && pnpm lint` (from `frontend/`)
Expected: PASS — no TypeScript errors, no lint errors. (`error`/`profile` state is still declared and used in `handleSubmit`, so no unused-variable errors.)

- [ ] **Step 3: Manual visual check**

Run: `pnpm dev` (from `frontend/`), open the printed local URL.
Expected (manual observation): dark page with a top bar showing the Scout logo + wordmark, a centered card below it containing the form, purple submit button. Resize the browser to a narrow (mobile) width and confirm the submit button becomes full-width and no horizontal scrollbar appears. Stop the dev server after checking.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/App.tsx
git commit -m "Rebuild page shell and form with shadcn Card/Input/Label/Button"
```

---

### Task 4: Rebuild the results area with shadcn primitives

**Files:**
- Modify: `frontend/src/App.tsx`

**Interfaces:**
- Consumes: `Tabs`/`TabsList`/`TabsTrigger`/`TabsContent` from `@/components/ui/tabs`, `Badge` from `@/components/ui/badge`, `Alert`/`AlertTitle`/`AlertDescription` from `@/components/ui/alert`, `Skeleton` from `@/components/ui/skeleton` (all produced by Task 1); the `loading`, `error`, and `profile` state and the `ScoutProfile`/`Classification` types from Task 3.

- [ ] **Step 1: Add the imports**

In `frontend/src/App.tsx`, add these imports alongside the existing ones from Task 3 (after the `Card` import block):

```tsx
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Skeleton } from '@/components/ui/skeleton'
```

- [ ] **Step 2: Add the error, loading, and results JSX**

In `frontend/src/App.tsx`, replace:

```tsx
          </CardContent>
        </Card>
      </main>
    </div>
  )
}
```

with:

```tsx
          </CardContent>
        </Card>

        {error && (
          <Alert variant="destructive" className="mt-6">
            <AlertTitle>Something went wrong</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {loading && (
          <Card className="mt-6">
            <CardHeader>
              <Skeleton className="h-5 w-40" />
            </CardHeader>
            <CardContent className="space-y-4">
              <Skeleton className="h-9 w-full" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-3/4" />
            </CardContent>
          </Card>
        )}

        {profile && !loading && (
          <Card className="mt-6">
            <CardContent className="pt-6">
              {profile.low_confidence && (
                <Alert className="mb-4 border-amber-500/50 text-amber-400 [&>svg]:text-amber-400">
                  <AlertTitle>Low confidence</AlertTitle>
                  <AlertDescription>
                    Limited public information was found for this company. Treat this brief as a
                    starting point, not a finished picture.
                  </AlertDescription>
                </Alert>
              )}

              <Tabs defaultValue="overview">
                <TabsList className="grid w-full grid-cols-3">
                  <TabsTrigger value="overview">Overview</TabsTrigger>
                  <TabsTrigger value="rationale">Rationale</TabsTrigger>
                  <TabsTrigger value="talking-points">Talking Points</TabsTrigger>
                </TabsList>
                <TabsContent value="overview" className="space-y-4">
                  <div className="flex items-center gap-2">
                    <Badge>{profile.classification.service_line}</Badge>
                    <span className="text-sm text-muted-foreground">
                      {Math.round(profile.classification.confidence * 100)}% confidence
                    </span>
                  </div>
                  <p className="whitespace-pre-line text-sm text-foreground">{profile.brief}</p>
                </TabsContent>
                <TabsContent value="rationale">
                  <p className="whitespace-pre-line text-sm text-foreground">{profile.rationale}</p>
                </TabsContent>
                <TabsContent value="talking-points">
                  <ul className="list-disc space-y-1 pl-5 text-sm text-foreground">
                    {profile.talking_points.map((point) => (
                      <li key={point}>{point}</li>
                    ))}
                  </ul>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        )}
      </main>
    </div>
  )
}
```

- [ ] **Step 3: Verify build and lint pass**

Run: `pnpm run build && pnpm lint` (from `frontend/`)
Expected: PASS — no TypeScript or lint errors.

- [ ] **Step 4: Manual visual check**

Run: `pnpm dev` (from `frontend/`), open the printed local URL, and against a running backend (or by temporarily checking the loading/error branches in React DevTools if the backend isn't running):
- Submit the form and confirm the skeleton placeholder appears while loading.
- Confirm a successful response renders the three tabs (Overview/Rationale/Talking Points), each equal width and full-width as a row.
- Confirm the classification `Badge` and confidence text appear in the Overview tab.
- At a narrow (mobile) width, confirm the tabs row doesn't overflow or wrap.
Stop the dev server after checking.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/App.tsx
git commit -m "Rebuild results area with shadcn Tabs/Badge/Alert/Skeleton"
```

---

### Task 5: Remove unused Vite boilerplate assets

**Files:**
- Delete: `frontend/src/App.css`
- Delete: `frontend/src/assets/react.svg`
- Delete: `frontend/src/assets/vite.svg`
- Delete: `frontend/src/assets/hero.png`

**Interfaces:**
- None — these files are not imported anywhere in `frontend/src/`.

- [ ] **Step 1: Confirm the files are unused**

Run (from the repo root): `git grep -n "App.css\|hero.png\|vite.svg\|react.svg" -- frontend/src`
Expected: no output (no references).

- [ ] **Step 2: Delete the files**

```bash
git rm frontend/src/App.css frontend/src/assets/react.svg frontend/src/assets/vite.svg frontend/src/assets/hero.png
```

- [ ] **Step 3: Verify build and lint pass**

Run: `pnpm run build && pnpm lint` (from `frontend/`)
Expected: PASS — deleting unreferenced files doesn't affect the build.

- [ ] **Step 4: Commit**

```bash
git commit -m "Remove unused Vite boilerplate assets"
```
