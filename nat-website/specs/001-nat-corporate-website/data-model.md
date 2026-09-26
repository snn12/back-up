# Phase 1 Data Model: NAT Corporate Website

Derived from spec.md's Key Entities section. Expressed as Prisma models (implementation detail
of the chosen ORM from research.md) — the shapes below are the contract; `prisma/schema.prisma`
in the tasks phase MUST match this document.

## Conventions

- **Translatable fields** (per FR-025) are stored as a JSON object keyed by locale:
  `{ "az": "...", "en": "...", "ru": "..." }`. Application code MUST read the visitor's active
  locale key and fall back to `az` when that key is absent or empty — never render a blank
  field. This applies to every field marked **(translatable)** below.
- All models include `createdAt`/`updatedAt` timestamps (omitted from the tables below for
  brevity) except where noted.
- `id` fields are UUIDs (`cuid()`/`uuid()` — implementation detail, not a contract requirement).

## PortfolioEntry

Represents a client/partner project NAT showcases (FR-008, FR-009, FR-010).

| Field | Type | Notes |
|---|---|---|
| id | string (PK) | |
| name | string | Not translatable — proper noun (e.g., "Riva Restaurant") |
| roleDescription | JSON **(translatable)** | Short descriptor, e.g., "NFC menyu həlli" / "NFC menu solution" |
| bio | JSON **(translatable)** | Longer case-study text |
| imageUrl | string | Points at an asset under `brand-assets/` or an uploaded file |
| externalUrl | string, nullable | e.g., `https://www.barberxosratov.az/` |
| socialLink | string, nullable | Per spec's "social/contact link" field |
| isActive | boolean, default `true` | Public site MUST only render `isActive: true` entries (Acceptance Scenario 2, User Story 3) |
| displayOrder | int | Manual ordering in carousel/marquee |

**Validation rules** (enforced server-side via `zod`, constitution Principle V / FR-016):
- `name`: required, 1–120 chars.
- `roleDescription.az`: required (AZ is the fallback locale, so it cannot itself be empty);
  `en`/`ru` optional.
- `imageUrl`: required, must resolve to an allowed asset path/uploaded-file reference.
- `externalUrl`/`socialLink`: if present, must be a well-formed URL.

**State transitions**: `isActive` toggled via the admin Switch component (FR of the "Switch /
Checkbox / Radio" UI requirement) — no other lifecycle states; hard delete is a separate,
irreversible admin action distinct from deactivation (Edge Cases: "temporarily hidden without
being deleted").

## PricingPlan

Represents a tier shown in Qiymətlər (FR-011).

| Field | Type | Notes |
|---|---|---|
| id | string (PK) | |
| tierName | JSON **(translatable)** | e.g., "Başlanğıc" / "Starter" |
| price | decimal | |
| currency | string, default `"AZN"` | Fixed per spec Assumptions; not per-locale |
| billingPeriod | string, nullable | e.g., "aylıq"/"monthly" — free text, not translated (paired with tierName context) or modeled as an enum in tasks phase |
| features | JSON **(translatable)** | Array of feature strings, keyed by locale: `{ "az": ["..."], "en": ["..."], "ru": ["..."] }` |
| displayOrder | int | |
| isFeatured | boolean, default `false` | Optional visual emphasis (e.g., "most popular" card), matching the Untitled-UI-inspired grid's featured-card pattern noted in project planning |

**Validation rules**:
- `tierName.az`, `features.az`: required (AZ fallback).
- `price`: required, ≥ 0.

## AdminUser

An NAT staff account (FR-012, FR-014, FR-023).

| Field | Type | Notes |
|---|---|---|
| id | string (PK) | |
| email | string, unique | Login identifier |
| passwordHash | string | Never the plaintext password; Auth.js Credentials provider hashes on write |
| lastLoginAt | DateTime, nullable | |
| createdByAdminId | string, nullable (FK → AdminUser.id) | Records which admin created this account; null only for the initial seed admin (Assumptions: first account provisioned outside the public UI) |

**Validation rules**:
- `email`: required, valid email shape, unique.
- Password (write-only, never stored raw): minimum length/complexity enforced at the
  Auth.js/zod layer before hashing.
- **Creation is server-side restricted to an authenticated admin session** (FR-023) — the
  create-admin Route Handler MUST verify an existing session before inserting a new AdminUser;
  there is no public endpoint that creates this row.

## ContactSubmission

A message from the public contact form (FR-015, FR-016, FR-024).

| Field | Type | Notes |
|---|---|---|
| id | string (PK) | |
| firstName | string | |
| lastName | string | |
| email | string | |
| phoneCountryCode | string | e.g., `"+994"` |
| phoneNumber | string | |
| message | string | |
| consentAccepted | boolean | MUST be `true` to persist (FR-015) |
| submittedAt | DateTime | |
| readStatus | enum(`unread`,`read`) default `unread` | Surfaced in admin dashboard (Clarification Q3) |
| emailNotificationSent | boolean, default `false` | Set `true` only after successful send; failure MUST NOT block persistence or the visitor-facing success state (FR-024) |

**Validation rules** (`zod`, applied server-side in the `app/api/contact/route.ts` handler):
- `firstName`/`lastName`: required, 1–80 chars.
- `email`: required, valid email shape.
- `phoneNumber`: required, digits matching the selected country's mask.
- `message`: required, 1–2000 chars, sanitized to strip any HTML/script content before storage
  (FR-016 — defends the admin dashboard that later renders this text).
- `consentAccepted`: required `true`.
- Submission endpoint is rate-limited per source (Edge Cases: rapid/duplicate submissions).

## Relationships

```text
AdminUser 1 ──creates──> * AdminUser   (self-referential, createdByAdminId)
```

`PortfolioEntry`, `PricingPlan`, and `ContactSubmission` have no foreign-key relationships to
each other or to `AdminUser` — they are independently admin-managed/visitor-generated records.
This keeps the schema intentionally flat, matching the "Scale/Scope" note in plan.md (small
business site, not a multi-tenant system).
