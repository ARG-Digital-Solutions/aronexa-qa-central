# AroNexa — Central QA Automation

**Single private, independent, Git-ready QA repository** for AroNexa. Keeps the previously authored Playwright suites while introducing verified, controlled tests for integrated Reception + Appointments synthetic frontend. This archive is intentionally **not** the AroNexa development repository.

## Scope and safeguards
- **Synthetic-only / localhost-only** browser testing. No live patient or PHI, no backend startup, no Flyway, no original Windows DB or production URLs.
- Keep earlier tests in `legacy/` **unchanged** for historical traceability. Existing legacy selectors may be stale; do not treat their failures as app bugs without reconciling source.
- Verified test coverage in `tests/verified`: 4 viewport/navigation tests + 4 synthetic-only functional workflows, with screenshots and HTML/JUnit artifacts.
- Archived C2 JUnit evidence catalogued under `evidence/`; tests remain in the product repository. CI invokes them only when a *separately authorized* backend workflow is configured; the default CI is frontend-only.
- GitHub Actions is prepared but will not run automatically until this package is pushed to a private GitHub repository and secrets are configured. A product-repo trigger is **only a proposal** in `integration-templates/`.

## Quick start (Windows, existing isolated frontend on port 5175)

Use **Node.js 22** and open a new PowerShell window:

```powershell
$qa = 'C:\Users\ganes\Application Development\AroNexa-QA-Central'
Set-Location $qa
npm.cmd ci --no-audit --no-fund
npx.cmd playwright install chromium
$env:ARONEXA_BASE_URL = 'http://127.0.0.1:5175/'
npx.cmd playwright test tests/verified --project chromium-desktop --workers=1
npx.cmd playwright show-report artifacts/playwright-report
```

Leave the isolated Vite development server running at `http://127.0.0.1:5175/`. Use only the **INT-R1 review worktree**, not the protected main dev checkout. The QA tests run against the web page; they never connect to the Windows database.

Alternatively: `& .\scripts\Invoke-AroNexa-QA.ps1 -Suite verified -BaseUrl 'http://127.0.0.1:5175/' -InstallDependencies`.

### Test selection
- `npx.cmd playwright test tests/verified/int-r1-responsive.spec.mjs`: 4 viewport + navigation cases.
- `npx.cmd playwright test tests/verified/int-r1-workflow.spec.mjs`: 4 synthetic workflow cases.
- `npx.cmd playwright test -c legacy/playwright.config.mjs`: pre-existing suites **for separate compatibility review**, not part of the default pass gate.
- `& .\scripts\Invoke-AroNexa-QA.ps1 -Suite models -AppReviewPath 'C:\Users\ganes\Application Development\AroNexa-INT-R1-Review'`: product frontend model tests from the isolated checkout (no backend).

### To create the remote private repository (one-time)

This ZIP includes a local initial Git commit but **not** an online GitHub repository, because remote repository creation is not available in this session. From the extracted folder, after setting up `gh` and authenticating to your GitHub organization:

```powershell
cd 'C:\Users\ganes\Application Development\AroNexa-QA-Central'
git status
gh repo create ARG-Digital-Solutions/aronexa-qa-central --private --source . --remote origin --push
```

If the organization disallows member repo creation, ask an org owner to create an empty private repository, then `git remote add origin <private-repo-url>` and `git push -u origin main`. Never run `git init` inside the original AroNexa application repo.

### Future automation
1. In the new QA repository, configure `ARONEXA_SOURCE_READ_TOKEN` with read-only access to the **private product repo**; do not commit it.
2. The included GitHub Actions workflow checks out the isolated selected code ref, runs frontend model tests, builds Vite and executes the verified browser suite. It is scheduled weekdays; triggers on QA pushes and manual dispatch, too.
3. If you authorize immediate testing on each *AroNexa application* PR, review and install the separate dispatch template from `integration-templates/` with its own narrowly-scoped token. This is not installed or active in either repository.
4. Keep acceptance evidence linked to **exact app SHA + QA SHA**, JUnit outcome, browser project, and timestamp. No merge or release authorization is implied by green QA.

See `docs/ARCHIVE_AUDIT.md`, `docs/TEST_INVENTORY.md` and `docs/TEST_GOVERNANCE.md`.
