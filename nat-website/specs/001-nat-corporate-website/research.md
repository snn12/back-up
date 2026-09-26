# Phase 0 Research: NAT Corporate Website

All Technical Context items were resolved with informed defaults rather than left as
`NEEDS CLARIFICATION`, given the extensive prior requirements-gathering (project plan,
constitution, spec). This document records the reasoning so the choices are auditable.

## Framework: Next.js 15 (App Router) + React 19

- **Decision**: Next.js App Router, TypeScript.
- **Rationale**: Single codebase serves both the public marketing pages and the `/admin`
  dashboard/API without a separate backend service; Server Components reduce client JS for the
  content-heavy marketing pages (helps SC-001/SC-002 responsiveness); Route Handlers under
  `app/api/` satisfy the contact-form and admin-CRUD needs directly. Matches the tech stack
  already agreed in the project's planning notes.
- **Alternatives considered**: Remix (comparable, but the project's spec-kit tooling and prior
  conversation already anchored on Next.js); a separate Express/Fastify backend + Vite frontend
  (rejected — unnecessary split for this scale, doubles deployment surface for no benefit at
  "single-digit admin users, hundreds of visits/day" scope).

## Styling: Tailwind CSS v4 with custom `@theme` design tokens

- **Decision**: Tailwind v4's CSS-native `@theme` block, populated with the Dala-derived token
  names (color, type scale, spacing, radius) mapped to NAT's own colors, duplicated for a light
  theme.
- **Rationale**: The Dala reference document (`brand-assets/design/DESIGN-reference-dala.md`)
  is itself expressed as CSS custom properties and a Tailwind v4 `@theme` block — reusing that
  shape directly minimizes translation error between the reference and the implementation, and
  Tailwind's utility classes keep component code close to the token names rather than
  hand-rolled CSS-in-JS.
- **Alternatives considered**: CSS Modules with plain custom properties (viable, more
  boilerplate per component); a component-kit like Chakra/MUI (rejected — their built-in
  component styling would fight the from-scratch, license-clean requirement in constitution
  Principle III).

## Data layer: PostgreSQL + Prisma

- **Decision**: Prisma ORM against PostgreSQL.
- **Rationale**: FR-008/FR-011 require durable, admin-editable PortfolioEntry and PricingPlan
  records; Prisma gives type-safe queries matching the TypeScript stack and a straightforward
  `seed.ts` path for FR-010's required seed data. Postgres (over SQLite) because common Next.js
  hosts (Vercel-style) provide no persistent local disk, and a small hosted Postgres instance
  (Neon/Supabase/Railway — the specific provider is a deployment decision, not a code dependency)
  is inexpensive at this scale.
- **Alternatives considered**: SQLite/libSQL (rejected primarily for host-persistence risk,
  though it remains a fallback if a host with persistent disk is chosen later — swapping the
  Prisma datasource is a low-cost change); a headless CMS (explicitly rejected earlier in
  project planning — user chose a self-written admin panel over external CMS).

## Auth: Auth.js (Credentials provider), session-based

- **Decision**: Auth.js v5 (`next-auth@beta`) with the Credentials provider, **JWT session
  strategy** (corrected during implementation from an earlier "database-backed sessions" note —
  Auth.js's database session strategy requires a persistence adapter shaped around its own
  User/Account/Session/VerificationToken tables, which is unneeded machinery for a
  Credentials-only, single-digit-admin setup; JWT is the standard pairing for Credentials
  provider and keeps AdminUser as the one source of truth instead of duplicating it).
- **Rationale**: Satisfies FR-012/FR-014/constitution Principle IV ("öz-yazılan" / self-written
  admin, no external CMS/identity SaaS) — Auth.js is a library embedded in the app, not a
  hosted third-party identity service, so it does not violate that constraint. Provides
  session-expiry and CSRF handling out of the box rather than hand-rolling cookie/session logic,
  reducing the attack surface for constitution Principle V.
- **Alternatives considered**: Fully hand-rolled session auth (rejected — reinventing
  well-trodden security-sensitive code is higher risk than using an audited library); a hosted
  auth SaaS like Clerk/Auth0 (rejected — introduces an external account-management dependency
  the user did not ask for and that conflicts with "öz-yazılan admin panel").

## Internationalization: next-intl

- **Decision**: `next-intl` with `app/[locale]/` segment routing, `messages/{az,en,ru}.json`.
- **Rationale**: FR-022 requires AZ/EN/RU with a visible switcher and an AZ default; next-intl
  is the current standard for App Router locale routing and integrates with Server Components
  (avoids shipping a large i18n runtime to the client). FR-025's per-locale admin content fields
  are modeled directly in Prisma (see data-model.md) rather than through next-intl's static
  message files, since that content is dynamic/admin-edited, not developer-authored UI copy.
- **Alternatives considered**: `next-i18next` (Pages Router-oriented, weaker App Router support);
  a single mixed-language page with client-side string swapping (rejected — fails FR-022's
  requirement for full static-text translation and clean URLs per locale).

## Email notifications: Resend (SMTP/Nodemailer as swappable fallback)

- **Decision**: Resend's API for the FR-024 contact-notification email, with the sender
  abstracted behind `lib/email.ts` so a SMTP/Nodemailer implementation can be substituted without
  touching calling code.
- **Rationale**: Simple API, generous free tier appropriate for a low-volume contact form,
  avoids needing to manage SMTP credentials/deliverability directly. Abstracting behind one
  module keeps the choice reversible.
- **Alternatives considered**: Raw SMTP via Nodemailer (kept as the documented fallback,
  since the exact mailbox/provider NAT will use is still an open operational detail per spec's
  Assumptions); AWS SES (rejected — unnecessary infrastructure account for this scale).

## Carousel: `embla-carousel-react`

- **Decision**: Install `embla-carousel-react` directly.
- **Rationale**: The user's own Carousel specification names this exact library as "what
  shadcn/ui's Carousel wraps." Verified independently: Embla Carousel is MIT-licensed and
  published standalone on npm — it is not part of Untitled UI PRO and carries no licensing
  conflict with constitution Principle III. Using it directly (rather than reimplementing
  scroll-snap carousel mechanics by hand) satisfies the spec's own suggested technical
  foundation.
- **Alternatives considered**: Hand-rolled `scroll-snap-type: x mandatory` (the spec's own
  named alternative) — kept as a fallback approach for the simpler partner-logo Marquee, which
  doesn't need Embla's paging/dot-indicator logic.

## Hero techniques: mouse-scrub video and scramble text — implemented from scratch

- **Decision**: No library for either; both implemented as small, self-contained modules per the
  technique already validated in project planning (rem-based reference-frame scaling, pin-based
  anchor layout, `requestAnimationFrame`-driven video seek loop, and a from-scratch scramble-text
  effect instead of GSAP's paid `ScrambleTextPlugin`).
- **Rationale**: Both techniques were already fully specified (algorithm-level detail) during
  requirements gathering from a reference technical prompt; constitution Principle III requires
  the free/from-scratch path for the scramble effect specifically. Neither needs an external
  dependency.
- **Alternatives considered**: GSAP core (free) for general animation easing — remains an option
  for the entrance choreography if hand-rolled Web Animations API code proves unwieldy during
  implementation, since GSAP core (unlike the Club GreenSock bonus plugins) carries no license
  restriction; deferred to the tasks phase as a non-blocking implementation choice.

## Testing: Vitest + React Testing Library + Playwright + axe-core

- **Decision**: Vitest/RTL for unit and component tests, Playwright for end-to-end flows,
  `@axe-core/playwright` wired into the e2e suite for automated accessibility checks.
- **Rationale**: Directly serves SC-005 (automated accessibility violations = 0) and gives
  executable coverage of the cross-cutting flows named in the spec's acceptance scenarios
  (contact submission, admin login/redirect, portfolio and pricing CRUD, language switch,
  reduced-motion fallback).
- **Alternatives considered**: Cypress (comparable; Playwright chosen for built-in
  multi-browser support and first-party axe integration).
