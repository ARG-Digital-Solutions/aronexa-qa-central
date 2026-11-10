# COMM-V1 — Independent Synthetic Feature QA Central Handoff

Tracking: QA Central issue #16. Review-only; not commercial release approval.

## Pinned PRs on 2026-11-10
| Plan | Product PR | SHA | Expected model cases |
| --- | --- | --- | --- |
| COMM_V1_T01 | Consultation #75 | 72638f1aa78e6f43c1043526c910c3656e81ebce | 14 |
| COMM_V1_T03 | Smart Rx + Ink #78 | 8b935abfb23ef818e248c2104e8fff55be5d6b52 | 23 |
| COMM_V1_T04 | Billing #79 | c95b50d261ef457e336abf22faab30b720202b28 | 21 |

These counts are expectations from product test files, not proof of independent execution.

## Before activating
- Obtain independent security and QA review. New GitHub Actions manual workflows are unavailable on GitHub until merged to QA Central main after owner authorization.
- The workflow requires the existing read-only ARONEXA_SOURCE_READ_TOKEN for private product repo metadata/checkout; it holds no commit-status write permission.
- Manually dispatch AroNexa COMM-V1 Independent Synthetic Feature QA with the plan choice, reviewed 40-character SHA and synthetic-only acknowledgement.
- Inspect exact-source test jobs, JUnit, Playwright artifacts and provenance. If a product PR head changes, repin via reviewed QA plan.
- Do not reuse the P01_T07_INT_REG_01 plan on these features.

## Independent checks
1. Validate exact source PR, SHA, source owner, base branch and eight approved file paths without running untrusted code in the token-bearing validation job.
2. Run source-coupled Node model tests on the immutable SHA from QA Central.
3. Run application typecheck/root build and separate feature Vite preview build.
4. Run independent Playwright test suites against a loopback-only, fictional, in-memory demo; capture failed screenshots, traces, JUnit and exact provenance.

## Outside the scope of this QA package
No live APIs, PostgreSQL RLS/security, production clinical sign-off, signature/PDF validation, banking/money transfer, Windows installer, NVDA manual review, original DB, migrations, deployments or commercial release.

## Cross-repository automation
This package deliberately does not change the privileged registration dispatcher, QA #11/#12, or Development #81. After it passes independent QA review, propose a separately security-reviewed controller extension to route only the three registered plans, verify child runs and correlate exact SHA and request statuses. No new application PR may be marked QA PASS merely because this proposal exists.
