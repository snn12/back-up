# Feature Specification: NAT Corporate Website

**Feature Branch**: `001-nat-corporate-website`

**Created**: 2026-09-15

**Status**: Draft

**Input**: User description: "NAT (New Age Technology) korporativ vebsaytı — Next.js/React, çoxsəhifəli. NAT restoran/kafelər üçün rəqəmsal menyu həlləri (NFC kart + QR kod) və biznes vebsaytları hazırlayır. Ana səhifə (hero, xidmətlər, portfolio, qiymətlər, haqqımızda, FAQ, əlaqə) + ayrıca /login, /signup, /admin (dashboard) route-ları. Admin-idarəli portfolio/qiymətlər, dark/light tema, əlçatan UI komponentləri, funksiya ilə paralel təhlükəsizlik."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Visitor discovers NAT and requests contact (Priority: P1)

A potential client (a restaurant, cafe, or other small business owner) lands on the NAT
homepage, understands within seconds what NAT offers (NFC menu, QR menu, website building),
sees credible proof of past work, checks indicative pricing, and can reach out through a
contact form or the FAQ answers their remaining doubts.

**Why this priority**: This is the entire reason the site exists — without it there is no lead
generation and nothing else matters. It must work standalone, even before any admin-managed
content exists (seeded with the two known examples: Riva Restaurant, Elnur Xosratov Barber).

**Independent Test**: Deploy only the public marketing pages with seeded/default portfolio and
pricing data (no admin panel yet) — a visitor can still browse every section and submit the
contact form successfully.

**Acceptance Scenarios**:

1. **Given** a visitor on any device width from 360px to 1920px, **When** they open the home
   page, **Then** they see the hero, and can reach Xidmətlər, Portfolio/Müştərilərimiz,
   Qiymətlər, Haqqımızda, FAQ, and Əlaqə either by scrolling or via the header nav.
2. **Given** a visitor on a narrow (mobile) viewport, **When** they tap the hamburger (☰) icon,
   **Then** the full navigation list opens and each link scrolls to or navigates to the right
   section.
3. **Given** a visitor viewing the Əlaqə section, **When** they fill in name, email, phone, and
   message and submit, **Then** they see a success confirmation (toast) and the submission is
   recorded; invalid input (e.g., malformed email) is rejected with an inline message before
   submission succeeds.
4. **Given** a visitor with `prefers-reduced-motion` enabled or JavaScript disabled, **When**
   they load the home page, **Then** all content (including the hero headline and video area)
   is still visible and legible, without requiring animation or interaction to reveal it.

---

### User Story 2 - Admin signs in and sees a dashboard (Priority: P2)

An NAT staff member with admin credentials navigates to the login page, signs in, and lands on
a dashboard giving an overview of the site's manageable content before drilling into any
specific section.

**Why this priority**: Every content-management capability (portfolio, pricing) depends on this
existing first; it is the smallest independently-shippable slice of the admin experience.

**Independent Test**: With only login + empty dashboard shell implemented (no portfolio/pricing
CRUD yet), an admin can authenticate and reach `/admin`, and an unauthenticated visitor is
redirected away from `/admin`.

**Acceptance Scenarios**:

1. **Given** valid admin credentials, **When** submitted on `/login`, **Then** the admin is
   redirected to `/admin` and sees a dashboard with sidebar navigation (Home, Dashboard,
   Portfolio/Əməkdaşlar, Pricing, Settings).
2. **Given** no active admin session, **When** a browser requests `/admin` directly, **Then**
   the request is redirected to `/login` and no admin content is exposed.
3. **Given** repeated failed login attempts from the same source, **When** the attempt count
   exceeds the allowed threshold, **Then** further attempts are rate-limited for a cooldown
   period.

---

### User Story 3 - Admin manages the client portfolio (Priority: P3)

From the dashboard, an admin adds a new client/partner project (e.g., a third case study after
Riva and Barber Xosratov), edits an existing one, or removes one — and the public
Portfolio/Müştərilərimiz section reflects the change without any code change or redeploy.

**Why this priority**: This is the concrete, named requirement that made a database and admin
system necessary in the first place; it is the primary ongoing value the admin area provides.

**Independent Test**: Building on User Story 2, an admin can perform create/edit/delete on a
portfolio entry and immediately see the result on the public site in a new browser tab.

**Acceptance Scenarios**:

1. **Given** the admin is on the Portfolio section of the dashboard, **When** they add a new
   entry with name, description/role, image, short bio, and a social/contact link, **Then** it
   appears in the public Portfolio/Müştərilərimiz carousel and in the dashboard's list (with an
   updated count badge).
2. **Given** an existing portfolio entry, **When** the admin edits its fields or marks it
   inactive (via a switch), **Then** the public site reflects the change (inactive entries are
   hidden from the public carousel) and a success toast confirms the save.
3. **Given** zero portfolio entries exist (e.g., all deleted), **When** a visitor views the
   Portfolio section, **Then** an empty state (icon + one-line explanation) is shown instead of
   a blank area, and the admin dashboard's list shows the same empty state with a primary
   "add new" action.

---

### User Story 4 - Admin manages pricing plans (Priority: P4)

From the dashboard, an admin edits the tiers, prices, and feature lists shown in the public
Qiymətlər section, replacing the initial default/placeholder pricing without a code change.

**Why this priority**: Explicitly requested as admin-editable, but less urgent than the
portfolio (NAT can launch with placeholder pricing, it cannot launch implying portfolio entries
that don't exist).

**Independent Test**: Building on User Story 2, an admin can change a plan's price or feature
list and see it reflected on the public Qiymətlər section immediately.

**Acceptance Scenarios**:

1. **Given** the admin is on the Pricing section of the dashboard, **When** they update a plan's
   price or feature list and save, **Then** the public Qiymətlər section shows the updated
   values on next load.
2. **Given** default/seeded pricing exists before any admin edit, **When** a visitor views
   Qiymətlər before the admin has made changes, **Then** they see clearly presented (if
   provisional) pricing rather than an empty section.

---

### User Story 5 - Visitor experiences the signature hero interaction (Priority: P5)

A visitor with a mouse and standard motion preferences experiences the hero's distinguishing
visual: an animated cloud of tiny colored particles forming an organic brain-like shape,
drifting on its own and responding to mouse movement, alongside a "decoding" text reveal of the
NEW AGE TECHNOLOGY sub-brand line.

**Decision history**: originally specified as a mouse-scrub NFC-tap video (see
`nfc-tap-scrub.mp4` in `brand-assets/video/`, still available as a portfolio/case-study asset
elsewhere on the site). Superseded by this particle-constellation direction — carried over from
the Dala structural reference's signature imagery — per explicit user request after seeing the
static placeholder hero and asking for "the brain that reacts to mouse movement." The video
clip is NOT deleted and MAY be reused elsewhere (e.g., a Services or Portfolio illustration).

**Why this priority**: A polish/differentiation layer on top of User Story 1's functional hero;
the site is fully usable and the core value proposition is communicated without it, so it can
ship after the informational content is solid.

**Independent Test**: With User Story 1 shipped using a static hero (plain heading + still
background), this story can be validated in isolation by swapping in the particle visualization
and verifying idle animation, mouse-reactive movement, and the reduced-motion fallback each
work.

**Acceptance Scenarios**:

1. **Given** a desktop visitor with a fine pointer and standard motion preferences, **When** the
   hero loads, **Then** a particle cloud (small outlined triangles in NAT's teal/accent palette)
   forms a brain-like organic shape and animates continuously (ambient drift) even without
   pointer input.
2. **Given** the same visitor, **When** they move the mouse over the hero, **Then** the particle
   field visibly responds to the pointer position (e.g. parallax shift or local attraction/
   repulsion) rather than animating identically regardless of input.
3. **Given** a touch-only visitor, **When** the hero loads, **Then** the particle field still
   renders and animates on its own (ambient motion), since there is no pointer to react to.
4. **Given** `prefers-reduced-motion` is enabled, **When** the hero loads, **Then** the particle
   field renders as a static (non-animated) arrangement rather than looping motion, the entrance
   animation is skipped, and the sub-brand text renders instantly without the scramble effect.
5. **Given** a low-end device or a browser without Canvas/WebGL support, **When** the hero loads,
   **Then** the page degrades to the plain background color rather than showing a broken or
   blank region.

### Edge Cases

- What happens when the hero video fails to load (slow network, blocked request)? The headline,
  CTA, and nav must still be usable; the video area degrades to the page background color rather
  than showing a broken-media icon.
- What happens when an admin's session expires mid-edit? The next save attempt is rejected and
  the admin is prompted to sign in again without losing already-typed form content where
  reasonably possible.
- What happens when the same portfolio project needs to appear temporarily hidden without being
  deleted (e.g., a client asks to be removed from the public site temporarily)? Covered by the
  active/inactive switch in User Story 3.
- What happens when a visitor submits the contact form multiple times in quick succession
  (accidental double-click or scripted abuse)? The form and its backing endpoint are rate-limited
  per the security principle; a duplicate/rapid submission is rejected with a clear message
  rather than silently creating duplicate entries.
- What happens on a viewport narrower than the smallest tested breakpoint (very old/small
  devices)? Layout must not produce horizontal scroll or clipped content down to 360px width.
- What happens when someone tries to reach `/signup` or `/admin` without the required
  permission? See Clarification Q1 for the exact signup access model; in all cases `/admin`
  itself is never reachable without an authenticated session (User Story 2).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST present a public, multi-page website with a home page composed of
  Hero, Xidmətlər, Portfolio/Müştərilərimiz, Qiymətlər, Haqqımızda, FAQ, and Əlaqə sections, plus
  dedicated `/login`, `/signup`, and `/admin` routes — the site MUST NOT be a single scrolling
  page with no distinct routes for these functional areas.
- **FR-002**: The header navigation MUST list Home, Xidmətlər, Portfolio/Müştərilərimiz,
  Qiymətlər, Haqqımızda, FAQ, and Əlaqə, plus a dark/light theme toggle, and MUST collapse into a
  hamburger (☰) menu below 999px width or on coarse-pointer devices; `/admin` and `/login` MUST
  NOT appear in this primary navigation.
- **FR-003**: The footer MUST show the NAT logo with a short description, social network links,
  contact details (phone/email/address), a small admin/login link, and a copyright line — and
  MUST NOT include a quick-links column, legal/policy links, or a newsletter signup (explicitly
  excluded).
- **FR-004**: The site MUST support a dark theme and a light theme, defaulting to the visitor's
  `prefers-color-scheme`, with the visitor's explicit choice (once made) persisted across visits.
- **FR-005**: The hero section MUST occupy the full viewport height as a distinct section (not
  the entire site) and MUST NOT force the page to be non-scrollable beyond that section.
- **FR-006**: The hero MUST render an animated particle field (small outlined triangles in NAT's
  brand palette) forming an organic brain-like shape, with continuous ambient motion on all
  devices and additional mouse-reactive movement on pointer-capable devices; when
  `prefers-reduced-motion` is set, the field MUST render as a static (non-animated) arrangement
  and the entrance animation MUST be skipped. (Supersedes the originally specified mouse-scrub
  video; see User Story 5's decision history. The `nfc-tap-scrub.mp4` asset remains available for
  reuse elsewhere on the site.)
- **FR-007**: The "NEW AGE TECHNOLOGY" sub-brand text MUST render using a character-scramble
  reveal effect (random glyphs settling left-to-right into the final text) on capable devices,
  and MUST render the final text instantly (no scramble) when `prefers-reduced-motion` is set;
  the effect MUST be implemented without any paid third-party plugin.
- **FR-008**: The system MUST allow an authenticated admin to create, edit, and deactivate/delete
  portfolio (client/partner) entries, each with at minimum a name, a role/description, an image,
  a short bio, and a social/contact link.
- **FR-009**: The public Portfolio/Müştərilərimiz section MUST display only active portfolio
  entries, sourced from the admin-managed data store (not hardcoded), presented in a carousel
  (previous/next controls + position dots, no auto-rotation) and/or a continuously scrolling
  marquee for partner branding.
- **FR-010**: The system MUST seed the portfolio data store with the two known reference
  projects (Riva Restaurant, Elnur Xosratov Barber) so the public site is not empty at first
  launch.
- **FR-011**: The system MUST allow an authenticated admin to create, edit, and delete pricing
  plans (tier name, price, feature list), and the public Qiymətlər section MUST render these
  plans from the same data store, seeded with default/placeholder values until the admin edits
  them.
- **FR-012**: Access to `/admin` MUST require an authenticated admin session; unauthenticated
  requests MUST be redirected to `/login` without exposing any admin content or data.
- **FR-013**: The admin area MUST present a dashboard (overview + sidebar navigation: Home,
  Dashboard, Portfolio/Əməkdaşlar with sub-items and count badges, a divider, Pricing, Settings)
  rather than a bare set of CRUD forms with no overview.
- **FR-014**: Admin login MUST hash and never log or expose passwords in plaintext, MUST expire
  sessions after a reasonable period of inactivity, and MUST rate-limit repeated failed login
  attempts from the same source.
- **FR-015**: The contact form MUST collect first name, last name, email, phone (with country
  code selection), a message, and explicit consent to the privacy notice, and MUST NOT submit
  successfully without all required fields validated (correct email shape, non-empty message,
  consent checked).
- **FR-016**: All user-supplied input across the site (contact form, admin content fields, any
  query/search input) MUST be validated and sanitized server-side before storage or use, rejecting
  malformed input rather than silently accepting it.
- **FR-017**: No API key, database credential, or other secret MUST appear in frontend-delivered
  code or be committed to version control; such values MUST be read only from server-side
  environment configuration.
- **FR-018**: Every interactive component (toast, combobox/search, accordion, carousel, loading
  indicator, empty state, switch/checkbox/radio group) MUST implement the ARIA pattern specified
  for it (see project constitution Principle II) rather than a purely visual approximation.
- **FR-019**: The system MUST NOT include copied source code from Untitled UI PRO or GSAP Club
  GreenSock; where those products' reference material informed a component's layout or
  interaction, the component MUST be implemented from scratch using the project's own design
  tokens.
- **FR-020**: The FAQ section MUST be implemented as an accordion using native `<details>`/
  `<summary>` elements, allowing only one entry open at a time within the FAQ group.
- **FR-021**: The system MUST remain fully navigable via keyboard alone (tab order, visible
  focus, Escape/Arrow key support on the components that specify it) without requiring a mouse.
- **FR-022**: The site MUST support Azerbaijani, English, and Russian for all static UI text
  (navigation, buttons, section labels, FAQ, form labels/errors), with a visible language
  switcher accessible from the header; Azerbaijani is the default locale.
- **FR-023**: `/signup` MUST NOT allow open public self-registration; new admin accounts MUST be
  created only by an existing authenticated admin (e.g., from within `/admin`), and this
  restriction MUST be enforced server-side, not only hidden in the UI.
- **FR-024**: On successful contact form submission, the system MUST both persist the submission
  (queryable from the admin dashboard) AND send an email notification to NAT's configured inbox;
  if the email step fails, the submission MUST still be persisted and the visitor MUST still see
  a success confirmation (email delivery is not a condition for the visitor-facing success state).
- **FR-025**: Admin-managed content (PortfolioEntry text fields, PricingPlan name/feature list)
  MUST support per-locale text for Azerbaijani, English, and Russian; if a translation is missing
  for the visitor's selected language, the system MUST fall back to the Azerbaijani text rather
  than showing a blank field.

### Key Entities

- **PortfolioEntry**: A client/partner project NAT showcases (e.g., Riva Restaurant, Elnur
  Xosratov Barber). Attributes: name, role/description (per locale: AZ/EN/RU), image, short bio
  (per locale), social/contact link, active/inactive status, display order, created/updated
  timestamps.
- **PricingPlan**: A service tier shown in Qiymətlər. Attributes: tier name (per locale), price,
  currency (AZN), billing period (if any), feature list (per locale), display order.
- **AdminUser**: A NAT staff account permitted to sign in and manage PortfolioEntry and
  PricingPlan records, and to create further AdminUser accounts. Attributes: email/username,
  hashed password, last login timestamp. Created only by another AdminUser (FR-023), never via
  public self-registration.
- **ContactSubmission**: A message received through the public contact form. Attributes: name,
  email, phone, message, submitted timestamp, read/unread status, email-notification-sent flag.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A first-time visitor can name at least two of NAT's three core services (NFC
  menu, QR menu, website) after viewing only the hero and Xidmətlər section, without scrolling
  further.
- **SC-002**: A visitor can locate and successfully submit the contact form in under 60 seconds
  from landing on any page of the site.
- **SC-003**: An admin can publish a new portfolio entry to the live public site in under 2
  minutes from login, with zero code changes or redeploys.
- **SC-004**: An admin can update a pricing plan and see it live on the public Qiymətlər section
  immediately after saving, with zero code changes or redeploys.
- **SC-005**: The site has zero critical/serious automated accessibility violations (axe-core or
  equivalent) across the home page, login, and admin dashboard.
- **SC-006**: The site renders with no horizontal scroll and no clipped/overlapping content at
  any viewport width from 360px to 1920px.
- **SC-007**: A returning visitor's dark/light theme choice is still in effect on their next
  visit without re-selecting it.
- **SC-008**: With JavaScript disabled, 100% of the home page's textual content (including hero
  headline and sub-brand text) remains present and readable in the initial HTML response.
- **SC-009**: Before public launch, the site passes a full pass of the six agreed security-review
  prompts and a `strix` scan with zero unresolved high-severity findings.
- **SC-010**: A visitor can switch the site's language (AZ/EN/RU) in one action from any page,
  and 100% of static UI text (nav, buttons, section labels, FAQ, form) updates to the selected
  language immediately.

## Assumptions

- A single admin role is sufficient for launch; a multi-role permission system (e.g., separate
  "editor" vs "owner" access) is out of scope unless a future amendment requires it. The very
  first AdminUser account (before any admin exists to create one) is provisioned outside the
  public UI (e.g., a seed script or direct database entry during setup), not through `/signup`.
- Portfolio card fields are name, role/description, image, short bio, and a social/contact link,
  per the most recent discussion — understood to still be open to revision before this ships,
  not a final locked schema.
- Pricing currency is AZN (Azerbaijani manat), consistent with the reference example
  (barberxosratov.az) and NAT's home market; prices are not shown in multiple currencies even
  though the UI is trilingual.
- The clean, high-resolution NAT logo file is still pending; until supplied, the logo frame
  extracted from the opening seconds of the source promotional video may be used as a stand-in.
- Standard session-based authentication (not third-party SSO/OAuth) is sufficient for the admin
  login, consistent with a single small business's internal use.
- English and Russian translations of static UI text and seeded content (Riva, Barber Xosratov,
  default pricing) will be produced as part of implementation (machine-assisted, human-reviewed);
  no separate translation vendor is assumed.
- A single outbound email address/service is available to NAT for the contact-form notification
  (FR-024); provisioning that mailbox/service is a setup task, not a separate feature.

## Clarifications

### Session 2026-09-15

- Q: Does `/signup` allow open public self-registration for new admin accounts, or is it a
  placeholder with account creation restricted to existing admins only? → A: Restricted — only an
  existing admin can create a new admin account; `/signup` is not an open public registration
  flow.
- Q: Should the site support only Azerbaijani, or also English/Russian? → A: Trilingual — the site
  MUST support Azerbaijani, English, and Russian, with a visible language switcher.
- Q: Should contact form submissions be stored and reviewable in the admin dashboard, emailed
  directly to NAT's inbox only, or both? → A: Both — every submission is persisted (visible in
  the admin dashboard) AND triggers an email notification to NAT's inbox.
