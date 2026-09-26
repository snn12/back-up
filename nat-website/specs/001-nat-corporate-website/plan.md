# Implementation Plan: NAT Corporate Website

**Branch**: `001-nat-corporate-website` | **Date**: 2026-09-15 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-nat-corporate-website/spec.md`

## Summary

A trilingual (AZ/EN/RU), dark/light-theme, multi-page Next.js marketing site for NAT (New Age
Technology) — a company selling NFC/QR digital-menu and website-building services to
restaurants/cafes. The public site (home page with hero, services, portfolio, pricing, about,
FAQ, contact) is backed by a login-protected `/admin` dashboard through which staff manage the
client/partner portfolio and pricing plans, stored in a relational database. The design system is
structurally inspired by the "Dala" reference (dark-canvas, oversized type, borderless layout,
single-accent-color philosophy) reimplemented with NAT's own teal/dark-gray palette and full
light-theme tokens. All interactive components (combobox, accordion, carousel, toast, etc.) use
correct ARIA patterns from the start; no Untitled UI PRO or GSAP Club GreenSock source is copied.

## Technical Context

**Language/Version**: TypeScript 5.x, Node.js 20 LTS

**Primary Dependencies**: Next.js 16 (App Router — confirmed 16.3.5 at scaffold time; note its
`middleware.ts`→`proxy.ts` rename and fully-async `params`/`searchParams`, per the framework's
own bundled upgrade docs), React 19, Tailwind CSS v4 (design tokens as
`@theme` CSS variables, mapped from the Dala-derived + NAT-brand token set), `next-intl`
(AZ/EN/RU routing + translation), Prisma ORM, `embla-carousel-react` (MIT-licensed, the same
engine referenced in the user's carousel spec — installed directly, no licensing concern; distinct
from Untitled UI PRO), Auth.js (Credentials provider, self-hosted session auth — no third-party
identity SaaS), Resend (or SMTP via Nodemailer as a swappable alternative) for the contact-form
email notification, `zod` for server-side input validation (contact form, admin content forms).

**Storage**: PostgreSQL (via Prisma) — chosen over SQLite because typical Next.js hosts (Vercel
and similar) have no persistent local disk; a hosted Postgres provider (e.g., Neon/Supabase/
Railway — provider choice is a deployment-time decision, not a code dependency) is assumed.

**Testing**: Vitest + React Testing Library (unit/component), Playwright (end-to-end flows:
contact form submission, admin login, portfolio/pricing CRUD, language switch), `@axe-core/
playwright` (automated accessibility checks feeding Success Criteria SC-005).

**Target Platform**: Server-rendered web application, evergreen desktop + mobile browsers (no IE
support assumed), deployed to a Node-compatible host (Vercel or equivalent).

**Project Type**: Web application — Next.js full-stack (App Router route handlers/Server Actions
serve as the backend; no separate frontend/backend repos).

**Performance Goals**: Largest Contentful Paint under 2.5s on a simulated mid-tier mobile
connection for the home page; hero particle-field animation holds 60fps on mid-tier hardware and
responds to pointer movement within a single animation frame (per spec User Story 5, updated —
particle constellation, not the originally planned video scrub).

**Constraints**: Hero section MUST NOT block page scroll beyond itself (spec FR-005); all
motion MUST respect `prefers-reduced-motion` (constitution Principle II); zero secrets in
client-delivered bundles (constitution Principle V); every component MUST have both dark- and
light-theme tokens before being considered complete (constitution Principle I).

**Scale/Scope**: Small business marketing site — single-digit admin users, low tens of portfolio
entries, single-digit pricing plans, expected traffic in the hundreds/day range at launch. No
high-concurrency or large-dataset engineering is required; correctness, accessibility, and
maintainability dominate over raw throughput.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|---|---|---|
| I. Dual-Theme Design System | Tailwind `@theme` tokens defined for both dark and light, NAT colors not Dala's; no component ships with only one theme's tokens | **PASS** (plan) — enforced by defining both token sets in `app/globals.css` before any component work begins in tasks phase |
| II. Accessibility Is Structural | Each interactive component (combobox, accordion, carousel, toast, skeleton/spinner, switch/checkbox/radio, empty state) implements the exact ARIA pattern from the spec; `@axe-core/playwright` gate in CI | **PASS** (plan) — component list mapped 1:1 to spec's UI-component requirements; automated a11y test included in Testing |
| III. No Unlicensed Third-Party Code | No Untitled UI PRO / GSAP Club GreenSock package or copied source in dependencies; `embla-carousel-react` is independently MIT-licensed (verified, not part of Untitled UI) | **PASS** (plan) — dependency list contains no paid/unlicensed package |
| IV. Admin-Managed Content | PortfolioEntry and PricingPlan are Prisma-modeled DB tables edited via `/admin`, never hardcoded; dashboard shell (not bare forms) planned in Project Structure | **PASS** (plan) — see data-model.md (Phase 1) |
| V. Security With the Feature | `zod` validation at every input boundary from the start; secrets via server-only env vars (never `NEXT_PUBLIC_*` for credentials); Auth.js session handling includes password hashing, expiry, rate limiting on login route | **PASS** (plan) — see Technical Context Constraints; full 6-point audit + `strix` remains a post-launch gate (out of this plan's scope, tracked separately per spec SC-009) |

No violations requiring Complexity Tracking justification.

**Post-Phase-1 re-check**: `data-model.md`, `contracts/`, and `quickstart.md` introduce no new
dependencies or patterns beyond those already gated above (Prisma/Postgres, Auth.js, next-intl,
`embla-carousel-react`, Resend — all free/self-hosted-library, none copied from a paid product).
All five gates remain **PASS**.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
app/
├── [locale]/                      # next-intl locale segment: az | en | ru
│   ├── (marketing)/
│   │   ├── page.tsx                # home: Hero, Xidmətlər, Portfolio, Qiymətlər, Haqqımızda, FAQ, Əlaqə
│   │   └── layout.tsx              # header + footer shell for public pages
│   ├── login/page.tsx
│   ├── signup/page.tsx             # admin-only account creation, not public registration (FR-023)
│   └── admin/
│       ├── layout.tsx              # sidebar dashboard shell, session-gated
│       ├── page.tsx                # dashboard overview
│       ├── portfolio/page.tsx
│       ├── pricing/page.tsx
│       └── settings/page.tsx
├── api/
│   ├── contact/route.ts            # validate + persist + email notify (FR-024)
│   ├── auth/[...nextauth]/route.ts
│   ├── admin/portfolio/route.ts
│   └── admin/pricing/route.ts
└── globals.css                     # Tailwind @theme: dark + light token sets

components/
├── layout/ (Header, Footer, LanguageSwitcher, ThemeToggle)
├── hero/ (ParticleField, ScrambleText, PinLayout primitives)
├── ui/ (Toast, Combobox, Accordion, Carousel, Marquee, Skeleton, Spinner, EmptyState,
│        Switch, Checkbox, RadioGroup) — one ARIA-correct primitive per spec UI requirement
├── portfolio/ (PortfolioCard, PortfolioCarousel)
├── pricing/ (PricingCard, PricingGrid)
├── contact/ (ContactForm)
└── admin/ (Sidebar, DashboardStat, PortfolioForm, PricingForm)

lib/
├── db.ts (Prisma client)
├── auth.ts (Auth.js config)
├── validation/ (zod schemas: contact, portfolio, pricing)
├── i18n/ (next-intl config, message loaders)
└── email.ts (contact-notification sender)

prisma/
├── schema.prisma
└── seed.ts                         # seeds Riva + Barber Xosratov portfolio, default pricing (FR-010)

messages/
├── az.json
├── en.json
└── ru.json

brand-assets/                       # already populated (video/, design/) — unchanged by this plan

tests/
├── unit/
├── component/
└── e2e/ (Playwright: contact flow, admin auth, portfolio/pricing CRUD, i18n switch, a11y)
```

**Structure Decision**: Next.js App Router single project (no separate `frontend/`/`backend/`
split — Route Handlers under `app/api/` are the backend). Locale-prefixed routing under
`app/[locale]/` via `next-intl` covers FR-022; `admin/` and `login/`/`signup/` sit outside the
public `(marketing)` route group so they never inherit the marketing header/footer nor appear in
its nav, matching FR-002's requirement that admin/login stay out of primary navigation.

## Complexity Tracking

None — no constitution violations requiring justification (see Constitution Check above, all
gates PASS).
