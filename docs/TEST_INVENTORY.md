# Central test inventory

## Newly verified, default executable tests

| Test file | Cases | Target | Default CI |
|---|---|---|---|
| `tests/verified/int-r1-responsive.spec.mjs` | 4 (1440, 768, 390 and 320 pixel widths) | Navigation, page horizontal overflow, console errors and screenshots | Yes |
| `tests/verified/int-r1-workflow.spec.mjs` | 4 | Explicit registration/duplicate-review, booking/conflict/cancel/rebooking, reschedule/history, receptionist check-in | Yes |
| `tests/verified/r3a-accessibility.spec.mjs` | 12 (8 functional + 4 viewport) | Keyboard focus, accessible form errors, native modal, announcements, appointment labels/actions/history and responsive overflow | Yes; automated only |

R3-A automated tests run on the frozen synthetic app commit `52809efbc077cd6abb6860d870cc487cc8eddc42` when the central QA workflow uses its default app SHA. The QA workflow's manual/dispatch app-ref override may select a different revision; always record the tested SHA. **No claim of screen-reader acceptance:** NVDA/VoiceOver review with a human remains pending. The QA workflow uses only a localhost Vite server, never the backend/DB. R3-A originated from the dedicated Windows test kit and has been adapted to the existing central Playwright runner (`.mjs`), avoiding a new standalone local test harness.

## Pre-existing Playwright test files preserved without modification

- `legacy/tests/dashboard.spec.mjs` — dashboard + appointment surface smoke
- `legacy/tests/registration.spec.mjs` — registration paths
- `legacy/tests/appointments.spec.mjs` — booking paths
- `legacy/tests/extended-actions.spec.mjs` — cancellation/reschedule/check-in adapters (provisional)
- `legacy/tests/responsive.spec.mjs` — prior basic mobile/tablet assertions
- `legacy/tests/p01-t07-reception.spec.mjs` — QA-001–003
- `legacy/tests/p01-t07-appointments.spec.mjs` — QA-004–007 (disposable backend guard)

**Count:** 7 `.spec.mjs` files in the QA suite archive (dashboard, registration, appointments, extended, responsive, P01-T07 Reception, P01-T07 Appointments); `legacy/` contains these exactly. Earlier message's 8-file count was overcounted; this inventory is based on filenames verified in the archive. Legacy suite compatibility is not asserted.

## Existing source model and backend tests (not copied as independent runnable suites)
- `reference/int-r1-model-tests/` — prior Reception + Appointment Node.js tests, retained as reference only; run active copies from pinned AroNexa checkout.
- `evidence/c2-backend-2026-11-08.json` — 18 backend JUnit classes/133 passing archived tests; run from AroNexa source with independent, disposable Postgres only under a separately authorized backend CI job.
- `evidence/legacy-browser-2026-11-08.json` — archived 69 skipped browser test executions; not evidence of pass.

## Adding tests
- Add new reviewed `*.spec.mjs` files under `tests/verified/` using `@playwright/test` and local synthetic app selectors; use descriptive test names and explicit fail-closed assertions.
- Tests which connect to backend/database must be placed in a **separate gated workflow** and require disposable DB approval. Never add a production URL or shared DB credential to browser CI.
- Existing test names/IDs should be reused rather than duplicated; identify feature + requirement ID and update this inventory.
