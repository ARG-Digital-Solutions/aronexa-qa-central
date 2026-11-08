# AroNexa central Playwright test-case catalog — draft v0.1

**State: AUTHORED, NOT EXECUTED** on the owner's latest uncommitted Agent-4 UI. The source of the local appointment screen was not uploaded, so initial selectors are candidates. A failed selector is not proof of a product bug until inspected.

| ID | Feature | Automated scenario | Tag | Current result |
|---|---|---|---|---|
| UI-C1-001 | Reception | Dashboard and synthetic safeguards visible | `@smoke @registration` | NOT RUN |
| UI-C1-002 | Registration | Required name validation visible | `@registration` | NOT RUN |
| UI-C1-003 | Registration | Register and find synthetic patient | `@registration` | NOT RUN |
| UI-C1-004 | Registration | Duplicate candidate review, no auto-merge | `@registration` | NOT RUN |
| UI-C1-005 | Registration | Modal Escape restores focus | `@registration` | NOT RUN |
| UI-C1-006 | Registration | Session-created patient clears on refresh | `@registration` | NOT RUN |
| UI-APT-001 | Appointments | Appointment screen and controls render | `@smoke @appointments` | NOT RUN |
| UI-APT-002 | Appointments | Booking creates demo token | `@appointments` | NOT RUN |
| UI-APT-003 | Appointments | Reject slot conflict | `@appointments` | NOT RUN |
| UI-APT-004 | Appointments | Search by demo token | `@appointments` | NOT RUN |
| UI-APT-005 | Appointments | Reject past date | `@appointments` | NOT RUN |
| UI-APT-006 | Appointments | Cancel and release slot | `@extended` | NOT RUN — locator review |
| UI-APT-007 | Appointments | Reschedule and retain history | `@extended` | NOT RUN — locator review |
| UI-APT-008 | Appointments | Check-in updates queue | `@extended` | NOT RUN — locator review |
| UI-RESP-001 | Responsive | Reception controls without page overflow | `@responsive` | NOT RUN |
| UI-RESP-002 | Responsive | Appointment controls accessible on viewport | `@responsive` | NOT RUN |

## Tag meanings

- `@smoke`: first page render and UI availability checks.
- `@registration`: receptionist patient registration workflow.
- `@appointments`: booking/search/validation workflow.
- `@responsive`: responsive checks, intended for all Chromium viewport projects.
- `@extended`: additional action cases needing source locator reconciliation before reliable results.
- `core`: everything except `@extended`.
- `all`: includes all provisional extended checks.

## Evidence boundaries

The earlier **26 receptionist model tests** and **20 appointment model tests** are *Node model tests*, not browser automation. Do not add them to Playwright pass totals. Previous manual browser checks are separate owner evidence. No new Playwright PASS is established until a real run is recorded.

## Coverage to add later

Screen-reader (NVDA) evidence; 200% zoom; filtered appointment cancellation/reschedule; timezone-specific browser date; concurrent real-user reservations; tenant/branch/role security; server persistence; patient communications; real data/privacy governance; OPD/IPD/pharmacy/billing once separately implemented.

## Formal result log template

Record: local run date/time/timezone; target localhost URL; browser and viewport; current repo SHA; Git diff status/hash of uncommitted source; exact command; PASS/FAIL/SKIP count; screenshots/trace location; open defects vs locator defects; owner acceptance decision; no customer release claim; issue #31/#45 gate retained.
