# Quickstart: NAT Corporate Website

Validation guide for proving the feature works end-to-end once implemented. Not an
implementation guide — see `data-model.md` and `contracts/` for the shapes involved, and
`tasks.md` (produced by `/speckit-tasks`) for the build steps themselves.

## Prerequisites

- Node.js 20 LTS, npm
- A reachable PostgreSQL instance (local via Docker, or a hosted dev database) and its
  connection string
- Environment variables (server-only, never `NEXT_PUBLIC_*` — constitution Principle V):
  `DATABASE_URL`, `AUTH_SECRET`, an email-provider credential (e.g., `RESEND_API_KEY`)

## Setup

```bash
npm install
npx prisma migrate dev
npx prisma db seed          # loads Riva + Barber Xosratov portfolio, default pricing (FR-010)
npm run dev
```

## Scenario 1 — Public visitor journey (User Story 1)

1. Open `http://localhost:3000/az` (default locale). Confirm the header shows Home, Xidmətlər,
   Portfolio/Müştərilərimiz, Qiymətlər, Haqqımızda, FAQ, Əlaqə, plus a theme toggle and a
   language switcher.
2. Resize the viewport below 999px (or use a touch/coarse-pointer emulation). Confirm the nav
   collapses to a ☰ button that opens/closes the full link list.
3. Scroll to Qiymətlər — confirm the seeded default pricing plans render as a card grid (not
   empty).
4. Scroll to Portfolio/Müştərilərimiz — confirm both seeded entries (Riva Restaurant, Elnur
   Xosratov Barber) appear in the carousel with working previous/next controls and no
   auto-rotation.
5. Fill and submit the Əlaqə form with valid data — expect a success toast. Submit again with an
   invalid email — expect an inline validation error, no submission recorded.
6. Switch the language to `en`, then `ru` via the switcher — confirm nav labels, section
   headings, and FAQ text change; the seeded portfolio/pricing content falls back to Azerbaijani
   for any field not yet translated (FR-025).
7. Enable `prefers-reduced-motion` (OS or browser devtools emulation) and reload — confirm the
   hero's particle field renders as a static (non-animated) arrangement, no scramble animation
   plays, and all text is still present with JavaScript disabled.

## Scenario 2 — Admin login and dashboard (User Story 2)

1. Navigate to `/az/login`. Attempt login with an invalid password 6+ times in a row — confirm
   the account is temporarily rate-limited.
2. Log in with the seeded admin credentials — confirm redirect to `/az/admin` showing a
   dashboard (not a bare form) with the sidebar (Home, Dashboard, Portfolio/Əməkdaşlar with a
   count badge, divider, Pricing, Settings).
3. Open a private/incognito window and request `/az/admin` directly with no session — confirm
   redirect to `/login` with no dashboard content flashed.

## Scenario 3 — Admin manages portfolio (User Story 3)

1. From the dashboard, add a new portfolio entry with all required fields.
2. In a separate tab, load the public Portfolio section — confirm the new entry appears without
   restarting the server.
3. Toggle the entry's active Switch off — confirm it disappears from the public carousel but
   remains listed (as inactive) in the admin dashboard.
4. Delete every portfolio entry — confirm the public section now shows the Empty State
   (icon + one line + primary action) instead of a blank area, and the dashboard list shows the
   matching empty state.

## Scenario 4 — Admin manages pricing (User Story 4)

1. Edit an existing plan's price and feature list; save.
2. Reload the public Qiymətlər section — confirm the new values are live with no redeploy.

## Scenario 5 — Hero interaction (User Story 5, updated 2026-09-15 — particle field, not video scrub)

1. Load `/az` — confirm an animated cloud of small outlined triangles (NAT teal palette) forms
   an organic, brain-like shape over the hero background and keeps drifting on its own (ambient
   motion) even before any pointer input.
2. On a desktop browser with a mouse, move the pointer across the hero — confirm nearby particles
   visibly shift away from the cursor (local repulsion) rather than animating identically
   regardless of input.
3. Using browser devtools' touch/mobile emulation, reload — confirm the particle field still
   renders and animates ambiently (no pointer-reactive behavior expected, since there is no
   pointer to read).
4. Confirm the "NEW AGE TECHNOLOGY" sub-brand text performs its character-scramble reveal on
   first load (motion enabled) and renders instantly with motion reduced (already covered in
   Scenario 1, step 7, where the particle field also freezes to a static arrangement).

## Automated checks (tie back to Success Criteria)

```bash
npm run test:unit        # Vitest + RTL
npm run test:e2e         # Playwright: contact flow, admin auth, CRUD, i18n switch
npm run test:a11y        # @axe-core/playwright — zero critical/serious violations (SC-005)
```

Manual/deferred: the full 6-point security-prompt audit and a `strix` scan are run once the
site is feature-complete, per constitution Principle V / spec SC-009 — out of this quickstart's
scope.
