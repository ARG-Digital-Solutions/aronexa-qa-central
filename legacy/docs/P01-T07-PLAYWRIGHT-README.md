# AroNexa P01-T07 — browser QA add-on (7 tests)

## Scope / provenance

- `QA-001` through `QA-003`: implemented against **inspected** GitHub branch `feature/p01-t07c1-reception-demo`, using visible accessible text and form IDs, with optional `data-testid` fallbacks.
- `QA-004` through `QA-007`: **proposed** browser cases for the more recent integrated appointment worktree; its local source and DOM were not available. Adapt the selector contract in `P01-T07-TEST-SELECTOR-CONTRACT.md` to that worktree. Do not claim PASS until run evidence is collected.
- Neither the local Windows app nor this private test folder was accessed. This is a non-destructive add-on, not a modification of existing files.

## Installation into existing suite

Copy the contents of this package as follows, **without overwriting** your existing `playwright.config.mjs`, `package.json`, `support/` files, or `tests/` files:

```
AroNexa-QA-Automation/
  playwright.config.mjs                 # keep existing
  package.json                          # keep existing
  tests/
    p01-t07-reception.spec.mjs          # new
    p01-t07-appointments.spec.mjs       # new
  support/
    p01-t07-helpers.mjs                 # new
  docs/
    P01-T07-PLAYWRIGHT-README.md       # this file
    P01-T07-TEST-SELECTOR-CONTRACT.md
```

Prerequisite: the existing test suite already has `@playwright/test` (version 1.33 or later) and Playwright browser binaries installed. Run `npx playwright --version` to check.

**Windows PowerShell commands** (use separate terminals for Vite and Playwright):

```powershell
$qa = 'C:\Users\ganes\Application Development\Testing Suite AroNexa\AroNexa-QA-Automation'
Set-Location $qa
$env:ARONEXA_BASE_URL = 'http://127.0.0.1:5174/'

# Initial safe run: synthetic, in-memory reception tests only
npx playwright test tests/p01-t07-reception.spec.mjs --headed --reporter=list

# To list all seven, including gated appointment cases
npx playwright test tests/p01-t07-*.spec.mjs --list

# Run appointments ONLY AFTER verifying the backend is disposable and synthetic-only.
$env:ARONEXA_QA_DISPOSABLE_CONFIRMED = 'YES'
npx playwright test tests/p01-t07-*.spec.mjs --headed --workers=1 --reporter=list

# Remove the intentional write authorization from the current terminal when done.
Remove-Item Env:ARONEXA_QA_DISPOSABLE_CONFIRMED
```

Note: `npx playwright test tests/p01-t07-*.spec.mjs` may match differently depending on the version/terminal. If in doubt, use `npx playwright test tests/p01-t07- --headed --workers=1 --reporter=list`.

If Playwright's current config uses a different baseURL, this package reads `ARONEXA_BASE_URL` directly and does not overwrite that config. It rejects URLs outside localhost/127.0.0.1. Browser requests that mutate remote addresses are blocked. **Still inspect the running application's DB connection settings** before appointment tests: a localhost backend can itself point to a shared/original database.

## Authentication

If your integrated worktree needs Receptionist authentication, reuse the existing suite's authenticated fixture or `storageState` and ensure it is scoped to a synthetic QA tenant. Do not embed passwords or tokens in specs. The C1 demo has no login.

## Date and slot assumptions

- All tests create unique synthetic patient names, without a phone number or health information.
- Appointment booking picks the first *enabled* slot offered by the UI. Nothing is hardcoded about slot times.
- Check-in explicitly books an appointment dated **today in Asia/Kolkata**. A test failure when no such slot is available is evidence that the acceptance precondition was not fulfilled; arrange an isolated test slot in the QA fixture rather than hardcoding an impossible time.
- The runner must use a synthetic/isolated tenant and disposable database. Afterward, reset the test database through your approved existing procedure.
- Do not connect to original/shared development or production databases or send live messages.

## Evidence

Your existing `playwright.config.mjs` may write `artifacts/results.xml`, screenshots and traces. Preserve those settings. For focused CLI evidence:

```powershell
npx playwright test tests/p01-t07- --workers=1 --reporter=list,junit
```

Review the CLI results, screenshot/trace evidence, and expected 7 test IDs. A skipped appointment test is **not** acceptance PASS. Approval, merge, migration and deployment remain out of scope.

## Recommended maintenance

Keep the seven QA cases in the external QA repo and update the `data-testid` contract whenever the React UI changes. Avoid XPath, brittle CSS styles, arbitrary sleeps, or dependence on another test's patient data.
