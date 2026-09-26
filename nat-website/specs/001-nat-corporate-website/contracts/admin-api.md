# Contract: Admin API

All routes below require an authenticated Auth.js session (FR-012). An unauthenticated request
to any route in this document MUST receive `401` (API calls) or a redirect to `/login` (page
navigations) and MUST NOT leak whether the requested resource exists.

## Authentication

### `POST /api/auth/callback/credentials` *(Auth.js-managed)*

**Request body**: `{ "email": "string", "password": "string" }`

**Responses**: Auth.js-standard — success sets a session cookie and redirects; failure returns a
generic authentication-failed response (never reveals whether the email exists, to avoid
account enumeration). Repeated failures from the same source are rate-limited (FR-014).

### `POST /api/admin/users` — create a new admin account

Implements FR-023: restricted to an existing authenticated admin; no public equivalent exists.

**Request body**: `{ "email": "string, required", "password": "string, required" }`

**Responses**:

| Status | Condition |
|---|---|
| 201 | Created; response excludes `passwordHash` |
| 401 | No valid admin session |
| 400 | Validation failure (weak password, malformed email, email already in use) |

## Portfolio

### `GET /api/admin/portfolio`

Returns all PortfolioEntry rows (active and inactive) for the dashboard list, including the
count used for the sidebar badge (FR-013).

### `POST /api/admin/portfolio`

**Request body**: matches `data-model.md`'s PortfolioEntry fields (`name`, `roleDescription`
per-locale, `bio` per-locale, `imageUrl`, `externalUrl?`, `socialLink?`, `displayOrder`).
`isActive` defaults to `true`.

**Responses**: `201` + created entity; `400` with field errors on validation failure; `401` if
unauthenticated.

### `PATCH /api/admin/portfolio/:id`

Partial update — any subset of the writable fields above, including `isActive` (the Switch
toggle) and `displayOrder`. `200` + updated entity; `404` if id doesn't exist; `400`/`401` as
above.

### `DELETE /api/admin/portfolio/:id`

Hard delete (distinct from deactivating via `isActive`, see data-model.md's State transitions
note). `204` on success; `404`/`401` as above.

## Pricing

### `GET /api/admin/pricing`

Returns all PricingPlan rows ordered by `displayOrder`.

### `POST /api/admin/pricing`

**Request body**: matches `data-model.md`'s PricingPlan fields (`tierName` per-locale, `price`,
`currency` defaulting `"AZN"`, `billingPeriod?`, `features` per-locale array, `displayOrder`,
`isFeatured?`).

**Responses**: `201` + created entity; `400`/`401` as above.

### `PATCH /api/admin/pricing/:id`

Partial update, same shape rules as portfolio's PATCH. `200`/`404`/`400`/`401`.

### `DELETE /api/admin/pricing/:id`

`204`/`404`/`401`.

## Contact submissions (read-only surface for Clarification Q3)

### `GET /api/admin/contact-submissions`

Returns ContactSubmission rows, newest first, for the admin dashboard view. Supports optional
`?status=unread` filter. No POST/PATCH beyond a `readStatus` update:

### `PATCH /api/admin/contact-submissions/:id`

**Request body**: `{ "readStatus": "read" }` only — submissions are otherwise immutable.
`200`/`404`/`401`.
