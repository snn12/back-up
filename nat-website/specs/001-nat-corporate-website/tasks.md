---
description: "Task list for NAT Corporate Website implementation"
---

# Tasks: NAT Corporate Website

**Input**: Design documents from `/specs/001-nat-corporate-website/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md (all present)

**Tests**: A handful of key Playwright/axe tests are included per story (the plan's Technical
Context specifies Vitest/Playwright/axe as the testing stack and quickstart.md's scenarios map
directly to them) — this is not full TDD gating, but each story's critical path gets an
automated check.

**Organization**: Tasks are grouped by user story (US1–US5, from spec.md, in priority order) so
each can be implemented, tested, and demoed independently.

**Next.js 16 note**: The scaffolded project installed Next.js 16.3.5, not 15 as assumed in
plan.md's Technical Context — confirmed via the framework's own bundled `AGENTS.md`/upgrade
docs. Two breaking changes affect this task list: (1) `middleware.ts` → `proxy.ts` with an
exported `proxy()` function (T016 updated below); (2) `params`/`searchParams` in every
`page.tsx`/`layout.tsx`/`route.ts` are `Promise`s and MUST be `await`ed — this applies to every
task below that creates a file under `app/[locale]/...` or `app/api/.../[id]/route.ts`.

## Path Conventions

Next.js App Router single project, per plan.md's Project Structure: `app/`, `components/`,
`lib/`, `prisma/`, `messages/`, `tests/` at the repository root (`C:\Users\ad-1000\Desktop\nat website`).

---

## Phase 1: Setup

**Purpose**: Project initialization and basic tooling

- [X] T001 Initialize Next.js 15 (App Router) + TypeScript project at repo root, per plan.md's Project Structure (`app/`, `components/`, `lib/`, `prisma/`, `messages/`, `tests/`)
- [X] T002 Add core dependencies to `package.json`: `next`, `react`, `react-dom`, `typescript`, `tailwindcss@4`, `next-intl`, `prisma`, `@prisma/client`, `next-auth`, `zod`, `embla-carousel-react`, `resend`
- [X] T003 [P] Add dev/test dependencies: `vitest`, `@testing-library/react`, `@playwright/test`, `@axe-core/playwright`, `eslint`, `prettier`
- [X] T004 [P] Configure ESLint + Prettier for the project
- [X] T005 [P] Configure `tsconfig.json` with path aliases (`@/components`, `@/lib`, etc.)
- [X] T006 [P] Create `.env.example` documenting `DATABASE_URL`, `AUTH_SECRET`, `RESEND_API_KEY` as server-only variables — explicit comment that none of these may ever be prefixed `NEXT_PUBLIC_` (constitution Principle V)
- [X] T007 [P] Scaffold `app/globals.css` with Tailwind v4 `@theme` block containing BOTH a dark and a light token set (color, type scale 12–113px, spacing base-6, radius), mapped from `brand-assets/design/DESIGN-reference-dala.md`'s structure but using NAT's teal/dark-gray palette, not Dala's violet/amber (constitution Principle I)
- [X] T008 [P] Scaffold `messages/az.json`, `messages/en.json`, `messages/ru.json` with an initial key set for nav labels, footer, and common UI strings (values may be placeholders for en/ru at this stage — filled in Polish phase)
- [X] T009 Configure `next-intl` request config and `app/[locale]/` segment scaffold with `az` as default locale

**Checkpoint**: Project builds and runs (`npm run dev`) with an empty `app/[locale]/page.tsx`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure every user story depends on

**⚠️ CRITICAL**: No user story work may begin until this phase is complete

- [X] T010 Define `prisma/schema.prisma` with all four models from data-model.md: `PortfolioEntry` (name string 1–120 required; roleDescription Json translatable, az key required; bio Json translatable; imageUrl string required; externalUrl string? valid URL; socialLink string? valid URL; isActive boolean default true; displayOrder int), `PricingPlan` (tierName Json translatable az required; price Decimal ≥0 required; currency string default "AZN"; billingPeriod string?; features Json translatable az required; displayOrder int; isFeatured boolean default false), `AdminUser` (email string unique required valid-email; passwordHash string; lastLoginAt DateTime?; createdByAdminId string? self-relation), `ContactSubmission` (firstName/lastName string 1–80 required; email string required valid-email; phoneCountryCode/phoneNumber string required; message string 1–2000 required; consentAccepted boolean must-be-true; submittedAt DateTime; readStatus enum unread/read default unread; emailNotificationSent boolean default false)
- [ ] T011 Run `npx prisma migrate dev` to create the initial migration against the configured PostgreSQL `DATABASE_URL`
- [X] T012 [P] Implement Prisma client singleton in `lib/db.ts`
- [X] T013 [P] Configure Auth.js Credentials provider + database session strategy in `lib/auth.ts`, mounted at `app/api/auth/[...nextauth]/route.ts`; passwords hashed on write, never logged or returned in any response
- [X] T014 [P] Implement zod validation schemas in `lib/validation/contact.ts`, `lib/validation/portfolio.ts`, `lib/validation/pricing.ts`, `lib/validation/admin-user.ts`, each enforcing exactly the field constraints quoted in T010/data-model.md
- [X] T015 [P] Implement email-sender abstraction in `lib/email.ts` — a single `sendContactNotification()` function backed by Resend, with the provider swappable behind this one module (research.md decision)
- [X] T016 Implement `proxy.ts` (renamed from `middleware.ts` — Next.js 16 breaking change, see `AGENTS.md`/bundled upgrade docs) exporting a `proxy()` function that combines next-intl locale routing with an Auth.js session gate: any request under `/[locale]/admin` without a valid session redirects to `/[locale]/login`; `/[locale]/admin` and its subpaths are never rendered unauthenticated (FR-012)
- [X] T017 Implement root locale layout `app/[locale]/layout.tsx`: wires next-intl provider, and a theme provider that defaults to `prefers-color-scheme`, persists the visitor's explicit choice to `localStorage`, and exposes it to all descendants (FR-004)
- [X] T018 [P] Implement `components/layout/ThemeToggle.tsx` (dark/light switch, uses the theme provider from T017)
- [X] T019 [P] Implement `components/layout/LanguageSwitcher.tsx` (AZ/EN/RU, routes to the equivalent `/[locale]` path, FR-022)
- [X] T020 [P] Implement shared ARIA-correct primitives used by multiple stories: `components/ui/Toast.tsx` (`role="status"`, fixed corner, non-blocking, auto-dismiss only non-essential messages, timer pauses on hover/focus), `components/ui/Skeleton.tsx` and `components/ui/Spinner.tsx` (`aria-busy` region + `role="status"` spinner per known/unknown-geometry rule), `components/ui/EmptyState.tsx` (labelled `<section>`, icon + one line + one primary action; dynamic no-results variant uses `role="status"` without moving focus)
- [X] T021 [P] Write `prisma/seed.ts`: seeds one AdminUser (`createdByAdminId: null`, the pre-provisioned first account per spec Assumptions), two PortfolioEntry rows (Riva Restaurant — az text from Instagram/video source material; Elnur Xosratov Barber — referencing barberxosratov.az as the externalUrl), and at least two default PricingPlan rows (placeholder AZN pricing) — satisfies FR-010
- [ ] T022 Run `npx prisma db seed` and verify all four tables are populated

**Checkpoint**: Foundation ready — `npm run dev` shows an empty-but-themed shell, `/admin` correctly redirects unauthenticated visitors, seed data exists in the database.

---

## Phase 3: User Story 1 - Visitor discovers NAT and requests contact (Priority: P1) 🎯 MVP

**Goal**: A complete, navigable public marketing site (static hero for now — US5 upgrades it)
with working portfolio/pricing display (from seeded data) and a validated, rate-limited contact
form.

**Independent Test**: Deploy Phase 1+2+3 only; a visitor can browse every home-page section via
desktop or the hamburger-collapsed mobile nav, and successfully submit the contact form.

### Tests for User Story 1

- [ ] T023 [P] [US1] Playwright test in `tests/e2e/navigation.spec.ts`: desktop nav shows all 7 links + theme/language controls; below 999px width (or coarse pointer) the ☰ button opens/closes the full link list (quickstart Scenario 1, steps 1–2)
- [ ] T024 [P] [US1] Playwright test in `tests/e2e/contact.spec.ts`: valid submission shows a success toast and persists a `ContactSubmission` row; an invalid email is rejected inline with no row created (quickstart Scenario 1, step 5)
- [ ] T025 [P] [US1] `@axe-core/playwright` test in `tests/e2e/a11y-home.spec.ts` asserting zero critical/serious violations on the home page (feeds SC-005)

### Implementation for User Story 1

- [X] T026 [P] [US1] Implement `components/layout/Header.tsx`: nav items Home, Xidmətlər, Portfolio/Müştərilərimiz, Qiymətlər, Haqqımızda, FAQ, Əlaqə + `ThemeToggle` + `LanguageSwitcher`; collapses to a ☰ hamburger below 999px width or on coarse-pointer devices; `/admin`/`/login` are never listed here (FR-002)
- [X] T027 [P] [US1] Implement `components/layout/Footer.tsx`: logo + short description, social links, contact details (phone/email/address), one small admin/login link, copyright — explicitly no quick-links column, no legal/policy links, no newsletter signup (FR-003)
- [X] T028 [US1] Implement `app/[locale]/(marketing)/layout.tsx` composing Header + Footer around all public pages
- [X] T029 [P] [US1] Implement a static hero placeholder inside `app/[locale]/(marketing)/page.tsx`: full-viewport-height section (not the whole page — page still scrolls, FR-005) with the NAT tagline headline, CTA button, and a still background (no video/scramble/scrub yet — added in US5)
- [X] T030 [P] [US1] Implement `components/sections/Services.tsx` (Xidmətlər): NFC menyu, QR menyu, Vebsayt — icon + short description each, from the agreed Instagram-sourced copy
- [X] T031 [P] [US1] Implement `components/portfolio/PortfolioCard.tsx` and `components/portfolio/PortfolioCarousel.tsx` using `embla-carousel-react`: previous/next buttons + position dots, `role="region" aria-roledescription="carousel"` wrapper, each slide `role="group" aria-roledescription="slide"` with a "N of M" label, no auto-rotation (FR-009)
- [X] T032 [US1] Implement the Portfolio/Müştərilərimiz section as a server component reading `PortfolioEntry` where `isActive: true`, ordered by `displayOrder`, resolving each translatable field to the visitor's locale with fallback to `az` (FR-025); renders `EmptyState` when the result set is empty
- [X] T033 [P] [US1] Implement `components/pricing/PricingCard.tsx` and `components/pricing/PricingGrid.tsx`: label→heading→sub-text block above a responsive grid of tier cards (structural pattern only, no Untitled UI source — constitution Principle III)
- [X] T034 [US1] Implement the Qiymətlər section as a server component reading `PricingPlan` ordered by `displayOrder`, locale-resolved with `az` fallback
- [X] T035 [P] [US1] Implement `components/sections/About.tsx` (Haqqımızda) with NAT's company description
- [X] T036 [P] [US1] Implement the FAQ section as a native `<details>`/`<summary>` accordion (shared `name` attribute so only one entry is open at a time), no added `aria-expanded` (FR-020)
- [ ] T037 [P] [US1] Implement `components/ui/Combobox.tsx`: `role="combobox"` input + `role="listbox"` popup, synced `aria-expanded`/`aria-controls`, options `role="option"`, selection tracked via `aria-activedescendant` (focus stays in the input), Arrow/Enter/Escape support, no autofocus on mount
- [X] T038 [US1] Implement `components/contact/ContactForm.tsx`: first/last name (side by side), email, phone with country-code select, message textarea, privacy-consent checkbox, submit button; client-side validation mirrors the server zod schema from T014
- [X] T039 [US1] Implement `POST /api/contact` in `app/api/contact/route.ts` per `contracts/public-api.md`: validate via `lib/validation/contact.ts`, sanitize `message` (strip HTML/script) before persisting, persist via Prisma, call `lib/email.ts` (failure does not block the 201 response), rate-limit repeated submissions from the same source (429 on excess), return the documented 201/400/429/500 shapes
- [X] T040 [US1] Wire `ContactForm` success/failure to the `Toast` component from T020
- [ ] T041 [P] [US1] Implement `components/ui/Marquee.tsx`: CSS `@keyframes translateX(-50%)` over duplicated content (never the `<marquee>` tag), edge-fade masks, `animation-play-state` pause on hover, motion fully stopped under `prefers-reduced-motion`; use for a partner-logo strip alongside/within the Portfolio section
- [ ] T042 [US1] Verify (manually + via T025) that with JavaScript disabled every US1 section's text content is present in the raw HTML response (SC-008)

**Checkpoint**: User Story 1 is fully functional and independently testable/deployable with
seeded portfolio/pricing data and a static hero.

---

## Phase 4: User Story 2 - Admin signs in and sees a dashboard (Priority: P2)

**Goal**: An admin can authenticate and reach a dashboard shell; unauthenticated access to
`/admin` is impossible; a second admin account can be created only by an existing admin.

**Independent Test**: With only this phase added to Phase 1–2, an admin logs in and reaches
`/admin`'s dashboard; an unauthenticated request to `/admin` is redirected.

### Tests for User Story 2

- [ ] T043 [P] [US2] Playwright test in `tests/e2e/admin-auth.spec.ts`: valid login reaches `/admin` with the sidebar visible; an unauthenticated request to `/admin` redirects to `/login` with no dashboard content rendered; 6+ consecutive failed logins are rate-limited (quickstart Scenario 2)

### Implementation for User Story 2

- [ ] T044 [US2] Implement `app/[locale]/login/page.tsx`: email/password form posting to the Auth.js Credentials callback
- [ ] T045 [US2] Implement `app/[locale]/signup/page.tsx`: renders only for an already-authenticated admin session (otherwise redirects/denies) and creates accounts via T048's endpoint — no public self-registration path exists (FR-023)
- [ ] T046 [P] [US2] Implement `components/admin/Sidebar.tsx`: Home, Dashboard, Portfolio/Əməkdaşlar (expandable, sub-items + count badge), a divider, Pricing, Settings (FR-013)
- [ ] T047 [US2] Implement `app/[locale]/admin/layout.tsx`: session-gated (relies on T016 middleware as the enforcement layer, this is the visual shell), renders `Sidebar`
- [ ] T048 [US2] Implement `app/[locale]/admin/page.tsx` dashboard overview: summary stats (portfolio count, pricing-plan count) plus a "recent contact submissions" widget reading `GET /api/admin/contact-submissions?status=unread` (implemented next) with a `Skeleton` loading state
- [ ] T049 [US2] Implement `POST /api/admin/users` in `app/api/admin/users/route.ts` per `contracts/admin-api.md`: rejects any request without a valid admin session (401) before any other processing, validates via `lib/validation/admin-user.ts`, hashes the password, excludes `passwordHash` from the response
- [ ] T050 [US2] Add login-attempt rate limiting on the Auth.js Credentials callback (FR-014), keyed per source
- [ ] T051 [US2] Implement `GET /api/admin/contact-submissions` and `PATCH /api/admin/contact-submissions/[id]` (readStatus only) per `contracts/admin-api.md`, both session-gated

**Checkpoint**: User Story 2 is independently testable — login, dashboard shell, and admin-only
account creation all work without Portfolio/Pricing CRUD existing yet.

---

## Phase 5: User Story 3 - Admin manages the client portfolio (Priority: P3)

**Goal**: Full create/edit/deactivate/delete on portfolio entries from the dashboard, reflected
live on the public site.

**Independent Test**: Building on Phase 4, an admin adds/edits/deletes a portfolio entry and
confirms the change on the public Portfolio section in a separate tab.

### Tests for User Story 3

- [ ] T052 [P] [US3] Playwright test in `tests/e2e/admin-portfolio.spec.ts`: add → appears publicly and in dashboard list with an updated count badge; deactivate via Switch → hidden publicly, still listed as inactive in the dashboard; delete all → both public and dashboard views show `EmptyState` (quickstart Scenario 3)

### Implementation for User Story 3

- [ ] T053 [P] [US3] Implement `components/ui/Switch.tsx` (`<input type="checkbox" role="switch">`), `components/ui/Checkbox.tsx`, and `components/ui/RadioGroup.tsx` (same-`name` native radios) — each with a visible, clickable `<label>` and checked state exposed via the native control
- [ ] T054 [US3] Implement `GET`/`POST /api/admin/portfolio` in `app/api/admin/portfolio/route.ts` per `contracts/admin-api.md`, validated via `lib/validation/portfolio.ts`
- [ ] T055 [US3] Implement `PATCH`/`DELETE /api/admin/portfolio/[id]` in `app/api/admin/portfolio/[id]/route.ts` (PATCH supports partial updates including the `isActive` toggle and `displayOrder`; DELETE is a hard delete distinct from deactivation)
- [ ] T056 [US3] Implement `components/admin/PortfolioForm.tsx`: per-locale (az/en/ru) fields for `roleDescription`/`bio` (az required, en/ru optional), image upload/URL, `externalUrl`, `socialLink`, and the `Switch` for `isActive`
- [ ] T057 [US3] Implement `app/[locale]/admin/portfolio/page.tsx`: list view with the count badge feeding the Sidebar, `Skeleton` while loading, `EmptyState` (with a primary "add new" action) when zero entries exist
- [ ] T058 [US3] Wire portfolio create/edit/delete outcomes to `Toast` success/error feedback

**Checkpoint**: User Story 3 is independently testable and integrates cleanly with US1's public
Portfolio section (no changes required there beyond what T032 already reads from the database).

---

## Phase 6: User Story 4 - Admin manages pricing plans (Priority: P4)

**Goal**: Full create/edit/delete on pricing plans from the dashboard, reflected live on the
public Qiymətlər section.

**Independent Test**: Building on Phase 4, an admin edits a plan's price/feature list and
confirms the update on the public Qiymətlər section.

### Tests for User Story 4

- [ ] T059 [P] [US4] Playwright test in `tests/e2e/admin-pricing.spec.ts`: edit a plan's price/features → public Qiymətlər section reflects the change on next load (quickstart Scenario 4)

### Implementation for User Story 4

- [ ] T060 [US4] Implement `GET`/`POST /api/admin/pricing` in `app/api/admin/pricing/route.ts` per `contracts/admin-api.md`, validated via `lib/validation/pricing.ts`
- [ ] T061 [US4] Implement `PATCH`/`DELETE /api/admin/pricing/[id]` in `app/api/admin/pricing/[id]/route.ts`
- [ ] T062 [US4] Implement `components/admin/PricingForm.tsx`: per-locale `tierName`/`features` (az required, en/ru optional), `price`, `currency` (default AZN), `billingPeriod`, `isFeatured`
- [ ] T063 [US4] Implement `app/[locale]/admin/pricing/page.tsx` list view with `Skeleton`/`EmptyState` as in T057
- [ ] T064 [US4] Wire pricing create/edit/delete outcomes to `Toast` feedback

**Checkpoint**: User Story 4 is independently testable.

---

## Phase 7: User Story 5 - Visitor experiences the signature hero interaction (Priority: P5)

**Goal**: Replace US1's static hero placeholder with the Dala-derived animated particle
constellation (brain-like shape, ambient + mouse-reactive motion) and the scramble-text
sub-brand reveal, each correctly degrading for touch and reduced-motion visitors. **Updated
2026-09-15**: supersedes the originally planned mouse-scrub NFC video (see spec.md User Story 5
decision history) — `nfc-tap-scrub.mp4` stays in `brand-assets/video/` for reuse elsewhere,
not deleted.

**Independent Test**: Swap the US1 static hero for this implementation and verify ambient
particle motion, mouse-reactive movement, and reduced-motion fallback each independently
(quickstart Scenario 5, updated; plus Scenario 1 step 7).

### Tests for User Story 5

- [ ] T065 [P] [US5] Playwright test in `tests/e2e/hero-motion.spec.ts`: with `prefers-reduced-motion` emulated, the particle field renders as a static (non-animated) arrangement, the entrance animation is skipped, and the sub-brand text renders instantly without scrambling (quickstart Scenario 1 step 7 + Scenario 5 step 3)

### Implementation for User Story 5

- [X] T066 [P] [US5] ~~Implement the rem-based reference-frame scale system and pin-based anchor layout primitives~~ — not needed for the particle-field approach (no longer porting the MindAI pin-layout technique into the hero); superseded, see T067b
- [X] T067 [US5] ~~Implement `components/hero/ScrubVideo.tsx`~~ — superseded by T067b (particle constellation)
- [X] T067b [US5] Implement `components/hero/ParticleField.tsx`: HTML5 Canvas, particles sampled within a brain/organic-blob silhouette, small outlined triangles in NAT's teal-accent palette (not Dala's violet/amber), continuous idle drift via `requestAnimationFrame`, mouse-position-reactive offset/parallax on pointer-capable devices, static single-frame render (no rAF loop) under `prefers-reduced-motion`, graceful no-op (solid background only) when Canvas is unavailable
- [X] T068 [US5] Implement `components/hero/ScrambleText.tsx` for the "NEW AGE TECHNOLOGY" sub-brand line: `requestAnimationFrame`-driven per-character settle (no GSAP `ScrambleTextPlugin` — constitution Principle III), monospace/tabular-width font so layout never jitters, final string exposed via `aria-label` with the churning span `aria-hidden`, instant final-text render under `prefers-reduced-motion`
- [ ] T069 [US5] Implement the entrance animation choreography (Web Animations API: particle field fade-in → logo/nav → headline → blurb → CTA, staggered) gated on `document.fonts.ready` and skipped entirely under `prefers-reduced-motion`
- [X] T070 [US5] Replace the US1 static hero placeholder in `app/[locale]/(marketing)/page.tsx` with the composed `ParticleField` + `ScrambleText` hero, keeping the same headline/CTA copy

**Checkpoint**: All five user stories are independently functional; the site is feature-complete
per spec.md.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements spanning multiple stories, and final validation

- [ ] T071 [P] Translate all static UI strings into `messages/en.json` and `messages/ru.json` (nav, footer, FAQ, form labels/errors, section headings) — FR-022
- [ ] T072 [P] Add per-locale (en/ru) content for the two seeded portfolio entries and default pricing plans in `prisma/seed.ts`, re-seed
- [ ] T073 Run the full `tests/e2e` suite plus `@axe-core/playwright` across home, login, and admin dashboard; fix any critical/serious violation (SC-005)
- [ ] T074 Verify responsive layout (no horizontal scroll, no clipped content) from 360px to 1920px across the home page, login, and admin dashboard (SC-006)
- [ ] T075 Verify theme choice persists across a browser restart (SC-007) and language switch persists the same session's theme choice
- [ ] T076 [P] Grep the built client bundle for any of `DATABASE_URL`, `AUTH_SECRET`, `RESEND_API_KEY` to confirm no secret leaks into client-delivered code (constitution Principle V)
- [ ] T077 Run `quickstart.md` end-to-end manually as a final sign-off pass
- [ ] T078 [P] Write a short project `README.md` covering setup (`npm install`, `prisma migrate dev`, `prisma db seed`, `npm run dev`) referencing `quickstart.md` for validation

**Not included here (explicitly deferred per constitution Principle V / spec SC-009)**: the full
six-point security-prompt audit and the `strix` scan — these run once the site above is
feature-complete, as a separate pass, per the project's existing security-hardening plan.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies — start immediately
- **Foundational (Phase 2)**: depends on Phase 1 — BLOCKS every user story
- **User Stories (Phases 3–7)**: all depend on Phase 2 completion only
  - US1 (P1) has no dependency on US2–US5
  - US2 (P2) has no dependency on US1, US3, US4, US5
  - US3 (P3) depends on US2 existing (portfolio CRUD lives in the admin dashboard shell) but its *public-facing* half (T032) was already built in US1 and needs no changes
  - US4 (P4) depends on US2 the same way US3 does; independent of US3
  - US5 (P5) depends on US1's hero placeholder existing (T029) to replace, but not on US2/US3/US4
- **Polish (Phase 8)**: depends on whichever stories are in scope for the release being finalized

### Parallel Opportunities

- All `[P]` tasks within Phase 1 can run together (different files)
- All `[P]` tasks within Phase 2 can run together once T010–T011 (schema + migration) land
- Once Phase 2 is checkpointed, US1, US2, and US5's non-hero-swap prep could in principle start
  in parallel across a team; in practice US5 (T066–T070) is easiest done right after US1's hero
  placeholder (T029) exists, since it replaces that file
- US3 and US4 can be built in parallel by different people once US2's Phase 4 checkpoint is
  reached (they touch disjoint files: `portfolio/` vs `pricing/`)

---

## Parallel Example: User Story 1

```bash
# Once Phase 2 is checkpointed, these US1 tasks touch independent files and can run together:
Task: "Implement components/layout/Header.tsx"
Task: "Implement components/layout/Footer.tsx"
Task: "Implement components/sections/Services.tsx"
Task: "Implement components/portfolio/PortfolioCard.tsx and PortfolioCarousel.tsx"
Task: "Implement components/pricing/PricingCard.tsx and PricingGrid.tsx"
Task: "Implement components/ui/Combobox.tsx"
Task: "Implement components/ui/Marquee.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Phase 1 (Setup) → Phase 2 (Foundational) → Phase 3 (US1)
2. **STOP and VALIDATE**: run `tests/e2e/navigation.spec.ts`, `contact.spec.ts`,
   `a11y-home.spec.ts`; walk Quickstart Scenario 1 by hand
3. This is a demoable, deployable marketing site with seeded portfolio/pricing and a static hero
   — already delivers the core lead-generation value even before any admin tooling exists

### Incremental Delivery

1. Setup + Foundational → foundation ready
2. + US1 → **MVP**, deploy/demo
3. + US2 → admin can log in (no content management yet), deploy/demo
4. + US3 → admin manages portfolio live, deploy/demo
5. + US4 → admin manages pricing live, deploy/demo
6. + US5 → signature hero interaction replaces the static placeholder, deploy/demo
7. Phase 8 → translations, full a11y/responsive/security-leak verification, sign-off

### Team Strategy (if more than one implementer)

- One track: Setup + Foundational (must land first, blocks everyone)
- Then split: Track A = US1 (public site), Track B = US2 → US3/US4 in parallel (admin), Track C
  = US5 (hero) once US1's placeholder hero file exists to replace
