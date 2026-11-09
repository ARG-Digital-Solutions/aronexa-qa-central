# AroNexa — Central QA operating model

**Effective direction:** 2026-11-09 (owner request); review of workflow changes remains pending.  
**Canonical QA repository:** [ARG-Digital-Solutions/aronexa-qa-central](https://github.com/ARG-Digital-Solutions/aronexa-qa-central)  
**Application under test:** [ARG-Digital-Solutions/aronexa-healthcare-platform](https://github.com/ARG-Digital-Solutions/aronexa-healthcare-platform)

## Division of responsibilities

| QA Central (test control plane) | Product repository (implementation) |
|---|---|
| QA backlog/issues, independent test plans and traceability mapping | Product code, business logic and database migration source |
| Playwright, accessibility, API/contract test harnesses and future mobile/desktop test harnesses | Source-coupled JUnit, Node model and Testcontainers test classes needed to compile/run against exact source |
| Manual/scheduled GitHub Actions *orchestration*, pinned source checkout, regression execution | Minimal local source test fixtures; no changes to frozen app features without owner approval |
| Actual JUnit/Playwright/JUnit XML reports, artifacts and review evidence per run | App PRs reference QA Central's exact run URL and disposition |
| Independent review and QA sign-off recommendation | Owner retains merge, migration, deployment, security and release approval |

**All NEW AroNexa QA task coordination and reusable automation belong in QA Central**, unless the test necessarily compiles with product source (for example a Java unit/integration test). Such tests stay versioned next to the code, but their independent execution, acceptance evidence, tracking and QA sign-off are coordinated here. Do not copy production code into QA Central or move a test that cannot run independently.

## Governance and boundaries

1. One writable QA worktree/branch per authorized QA task. Parallel agents can inspect; don't concurrently edit shared QA fixtures or workflows.
2. QA Central cannot modify or merge product PRs, activate APIs, deploy, or touch original Windows/shared PostgreSQL. Every backend/database QA execution must use fresh disposable Testcontainers only.
3. No real patient data, credentials, tokens, screenshots with PHI, production URLs or original database dumps in test inputs, PRs, logs or uploaded artifacts.
4. Use **exact 40-character product SHA and QA SHA**, requirement IDs, suite/config, timestamp, CI job and run URLs for every result. Unexecuted ≠ PASS; skips and historical snapshots are not PASS.
5. Separate browser synthetic mode from signed-proof backend tests and production security reviews. A green synthetic test is not patient-release approval.
6. Do not weaken test assertions or remove security tests just to make a pipeline green. File defects in the product repository and link them from QA issues.
7. New task QA coverage is proposed in a draft QA PR; any workflow permission or cross-repository dispatch changes receive explicit review. No silent installs or PR auto-merges.
8. Track independent reviewer approval; the implementation author cannot independently approve own QA closure.
9. Leave the original database migration hold, V10 production migration hold, frontend integration hold and release hold in place unless separately lifted.

## Workflow for future feature increments

1. Register an issue in QA Central for **task ID, product PR, exact SHA, requirement IDs and acceptance criteria**.
2. Create QA-only branch and draft PR for new test harness, test plan or report format; no changes to product code from QA agents.
3. Run tests through an audited QA Central workflow or isolated local QA runner using exact source SHA and synthetic data. For backend tests require ephemeral PostgreSQL, Docker and no shared DB credentials.
4. Publish results/links in QA Central; attach JUnit, Playwright artifacts or checksums as suitable. Fail closed when dependencies or checks are missing.
5. Review independently, issue PASS / FAIL / BLOCKED / NOT_RUN disposition for each gate. Product PR may reference QA evidence but remains separate.
6. Owner explicitly approves any product merge, customer delivery, migration or deployment.

## Current suites and planned expansion

- Synthetic Reception + Appointments browser/regression: `.github/workflows/qa-synthetic.yml`, `tests/verified/`.
- P01-T07-INT-REG-01 contract, Testcontainers and frozen frontend: `.github/workflows/qa-int-reg01.yml` (manual, gated; **not active until QA workflow PR is merged after review**).
- Security / SQL least privilege / RLS / idempotency / logging: source-coupled backend tests orchestrated from QA Central, with independent security review.
- Accessibility / NVDA: QA issues and evidence; automated axe/keyboard checks can complement but do **not** claim human NVDA approval.
- OPD, IPD, Pharmacy, Billing, IVF/IUI, multi-tenancy, Android/macOS and offline desktop: add suites and a requirements matrix as feature-specific increments with separate approvals.

## Credentials and execution policy

- QA workflow secret `ARONEXA_SOURCE_READ_TOKEN`: private product repository **Contents: read** only. Never pass a token into Maven/npm/Playwright test process or save in artifacts.
- GitHub Actions on an ephemeral Ubuntu runner: no Windows host mount, no original DB host details, no persistent migration.
- Workflow dispatch requires explicit synthetic-only acknowledgement and exact backend SHA. The INT-REG01 workflow pins frozen frontend commit `52809efbc077cd6abb6860d870cc487cc8eddc42`; changing it requires QA review.
- `workflow_dispatch` on new workflow becomes available on GitHub Actions only after the reviewed workflow is on the QA repository default branch.

## Relationship to AroNexa Master Engineering Contract V3.0

Independent QA does not override the product engineering scope restrictions. A QA-only repository changes neither the authorized file inventory for P01-T07-INT-REG-01 in the product repo nor the prohibition on merge/deploy/database access. Product PR #64 remains DRAFT / NOT_READY until fresh execution and independent review evidence exist.
