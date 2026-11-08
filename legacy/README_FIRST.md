# AroNexa — Central Playwright Test Suite

**Status: CREATED / NOT EXECUTED AGAINST THE LOCAL APP.** Prepared from the owner's UI screenshots and the GitHub PR #36 baseline. Agent 4's updated `App.tsx` is local/uncommitted and was not supplied, so selectors must be checked on first execution.

## Goal

Keep all Playwright browser tests in **one independent folder**, reusable for registration, appointments, and future OPD/IPD/pharmacy/billing modules. This pack does not change any accepted AroNexa worktree.

Recommended Windows location:

    C:\Users\ganes\Application Development\AroNexa-QA-Automation

Do **not** extract inside `agent-02-reception-ui` or `agent-04-appointments`.

## First-time setup (download/network permission required)

Open PowerShell in the extracted QA folder:

    & '.\Setup-Playwright-QA.ps1'

This installs pinned `@playwright/test` version 1.65.0 in the QA folder and downloads Chromium to the normal Playwright user cache. It creates `package-lock.json` locally; keep that file for later reproducible `npm.cmd ci` runs. No application repository source is edited.

If PowerShell refuses to execute scripts, do not weaken the system execution policy. Instead read the script, or from the QA folder run:

    npm.cmd install --no-audit --no-fund
    .\node_modules\.bin\playwright.cmd install chromium

## Start AroNexa synthetic UI in terminal 1

    $appt = 'C:\Users\ganes\Application Development\AroNexa-Codex-Worktrees\agent-04-appointments'
    Set-Location "$appt\frontend"
    npm.cmd run dev -- --port 5173 --strictPort

Open only the exact URL Vite prints. No backend, database, Docker or original Windows data required.

## Run the Playwright suite in terminal 2

    Set-Location 'C:\Users\ganes\Application Development\AroNexa-QA-Automation'
    & '.\Run-AroNexa-Playwright.ps1' -Suite smoke
    & '.\Run-AroNexa-Playwright.ps1' -Suite registration
    & '.\Run-AroNexa-Playwright.ps1' -Suite appointments
    & '.\Run-AroNexa-Playwright.ps1' -Suite responsive -Project chromium-mobile
    & '.\Run-AroNexa-Playwright.ps1' -Suite core -Project all

First run `smoke` and review selectors before `core` or `all`. `@extended` cancellation/rescheduling/check-in adapters are provisional until compared with the current Agent 4 source:

    & '.\Run-AroNexa-Playwright.ps1' -Suite extended

Change `-BaseUrl` if Vite actually uses a different **localhost** port. Nonlocal addresses are rejected.

## Direct commands if PowerShell script execution is blocked

From the QA folder:

    $env:ARONEXA_BASE_URL='http://127.0.0.1:5173/'
    .\node_modules\.bin\playwright.cmd test --grep @smoke --project chromium-desktop
    .\node_modules\.bin\playwright.cmd test --list
    .\node_modules\.bin\playwright.cmd show-report artifacts/playwright-report

## Evidence and reports

- Catalog: `docs/TEST_CASE_CATALOG.md`
- HTML: `artifacts/playwright-report/index.html`
- JUnit: `artifacts/results.xml`
- Failure screenshots/traces/videos: `artifacts/test-results/`
- Explicit dashboard and appointment screenshots attach to their smoke cases inside the HTML report.

## Safety / lifecycle

Localhost-only, synthetic records only. Do not type actual patient information. Each test starts in a fresh Playwright browser context. No source code, PRs, databases, notifications or deployments are changed. The QA suite can later be versioned in its own private Git repository **only after separate authorization**, or moved under `qa/playwright/` with another explicit approval.

## First-run source mismatch is expected sometimes

Because Agent 4's current DOM is local and was not uploaded, exact accessible names may differ. If a test fails with "element not found", first check the UI and locator in `tests/` or `support/helpers.mjs`; do **not** treat that alone as an application defect. Use `@playwright/test` locators and assertions; avoid adding test-only attributes to the accepted application without a separate authorization.
