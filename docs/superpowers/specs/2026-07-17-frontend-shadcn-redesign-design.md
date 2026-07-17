# Frontend shadcn Redesign — Design

Restyles the existing single-page Scout frontend (`frontend/src/App.tsx`) with shadcn/ui: same form → results flow, no new routes, no backend changes.

## Scope

Redesign only. No new features, no routing, no state management library, no light-mode toggle. Explicitly out of scope: backend changes, deck generation, Notion write-back (unrelated to this doc — see `2026-07-15-scout-v1-design.md`).

## Visual direction

Dark, high-contrast, "internal ops tool" feel — dark-only theme, no toggle. Accent color pulled from the existing brand mark (`frontend/public/favicon.svg`, `#7e14ff`/`#863bff` purple) into the shadcn `--primary` token, so buttons/focus rings tie back to the existing logo instead of a generic shadcn default.

## Setup

Run the official `shadcn` CLI (`npx shadcn@latest init`) against the Vite + React 19 + Tailwind v4 project:
- Adds `components.json`, a `@/*` path alias (`tsconfig.app.json` + `vite.config.ts`), and CSS theme tokens.
- Adds deps: `clsx`, `tailwind-merge`, `class-variance-authority`, `lucide-react`.
- Theme tokens (`--background`, `--primary`, etc.) are seeded directly with a dark palette — no `next-themes`, no toggle/localStorage logic, since dark is the only theme.

Components installed via CLI: `button`, `input`, `label`, `card`, `tabs`, `badge`, `alert`, `skeleton`, `separator`.

## Layout — full app shell

A slim top bar (`border-b`, dark surface) with the Scout wordmark/small logo on the left. Below it, a centered content column (`max-w-2xl`, `px-4` at all breakpoints) with vertical padding that tightens on mobile (`py-6` → `sm:py-10`).

## Form

Wrapped in a `Card`: `CardHeader` holds the "Scout" title + existing description copy, `CardContent` holds:
- `Label` + `Input` for company name (placeholder: "Enter a company name")
- `Label` + `Input` for the optional note
- Submit `Button`

While loading, the button shows a spinning `lucide-react` `Loader2` icon + "Researching…" and is disabled, same behavior as today, just restyled.

## Results

A second `Card` appears below once a profile loads, containing a `Tabs` component with three tabs:
- **Overview** — service-line classification as a `Badge`, confidence % next to it, and the brief text.
- **Rationale** — the "why this angle fits" text.
- **Talking Points** — the bullet list.

`profile.low_confidence` renders as an amber-tinted `Alert` above the tabs. Fetch errors render as a destructive-variant `Alert` in the same position they occupy today.

## Loading state

On submit, in place of the results `Card`, show a `Skeleton`-based placeholder shaped like the tabbed card (title bar + a few text-line skeletons) so the layout doesn't jump when real data arrives.

## Mobile responsiveness

- **Top bar**: padding/logo size scale down at small widths; wordmark stays left-aligned — no nav to collapse, so no hamburger menu.
- **Content column**: `max-w-2xl`, `px-4` at every breakpoint so content never touches the edge.
- **Cards**: rely on shadcn's default compact padding; verified no fixed widths are introduced.
- **Tabs**: `TabsList` uses `grid grid-cols-3 w-full` instead of the shadcn default inline-flex, so the three tabs become equal-width touch targets that never overflow or wrap on narrow screens.
- **Submit button**: `w-full` on mobile, auto-width from `sm:` up.
- **Inputs/labels**: already full-width by default.

## Cleanup

Delete unused Vite-boilerplate leftovers, none of which are imported anywhere in `src/`:
- `frontend/src/App.css`
- `frontend/src/assets/react.svg`
- `frontend/src/assets/vite.svg`
- `frontend/src/assets/hero.png`
