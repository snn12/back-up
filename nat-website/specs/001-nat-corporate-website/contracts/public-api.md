# Contract: Public API

## `POST /api/contact`

Implements FR-015, FR-016, FR-024; validated against `data-model.md`'s ContactSubmission rules.

**Request body** (JSON):

```json
{
  "firstName": "string, required",
  "lastName": "string, required",
  "email": "string, required, valid email",
  "phoneCountryCode": "string, required, e.g. +994",
  "phoneNumber": "string, required",
  "message": "string, required, 1-2000 chars",
  "consentAccepted": true
}
```

**Responses**:

| Status | Body | Condition |
|---|---|---|
| 201 | `{ "ok": true }` | Submission validated and persisted. Email notification is attempted asynchronously — its failure does NOT change this response (FR-024). |
| 400 | `{ "ok": false, "errors": { "<field>": "message" } }` | One or more fields fail validation (zod). Field-level messages, no stack traces or internals exposed. |
| 429 | `{ "ok": false, "errors": { "_form": "Too many requests" } }` | Rate limit exceeded for the requesting source (Edge Cases: rapid/duplicate submissions). |
| 500 | `{ "ok": false, "errors": { "_form": "Unexpected error" } }` | Persistence itself failed (not the email step — see above). No internal detail leaked. |

**Security notes**: server-side validation is authoritative regardless of client-side checks
(constitution Principle V / FR-016); handler MUST NOT log the raw message body at a log level
retained long-term without redaction consideration, since it is user-submitted free text.

## `GET /api/health` *(optional, operational convenience)*

Simple liveness check for deployment monitoring; not part of the feature spec's functional
requirements but a low-cost addition consistent with constitution Principle V's "logging for
... unusual traffic patterns" guidance. Returns `{ "ok": true }`, no auth required, no
information disclosure beyond process liveness.
