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
- Before activation, create the QA Central environment `comm-v1-source-read` with selected deployment branches limited to the branch `main` and no tag rules. Store `COMM_V1_SOURCE_READ_TOKEN` only as an environment secret. Verify its fine-grained scope is the product repository alone, with Metadata, Contents and Pull requests read-only. Record the scope and branch restriction in the security review. Do not reuse the registration controller token.
- Only the trusted QA workflow uses the source token, for PR metadata and exact-SHA checkout. The test container receives selected frontend and QA files without Git metadata, runner credentials or a Docker socket. Locked dependencies install with lifecycle scripts disabled. All app tests, builds and browser execution then run with Docker networking disabled and the QA harness mounted read-only.
- Manually dispatch AroNexa COMM-V1 Independent Synthetic Feature QA with the plan choice, reviewed 40-character SHA and synthetic-only acknowledgement.
- Inspect exact-source test jobs, JUnit, Playwright artifacts and provenance. The workflow rechecks the PR identity, head, and base before publishing evidence. If a product PR head changes, repin via reviewed QA plan.
- Do not reuse the P01_T07_INT_REG_01 plan on these features.

## Independent checks
1. Validate exact source PR, SHA, source owner, base branch and eight approved file additions without running untrusted code in the token-bearing validation job.
2. Run source-coupled Node model tests on the immutable SHA from QA Central.
3. Run application typecheck/root build and separate feature Vite preview build.
4. Run independent Playwright against the built preview over loopback. The browser context blocks service workers, WebSockets, redirects and requests outside the local read-only preview. Capture failure screenshots, traces, JUnit and exact provenance.

## Outside the scope of this QA package
No live APIs, PostgreSQL RLS/security, production clinical sign-off, signature/PDF validation, banking/money transfer, Windows installer, NVDA manual review, original DB, migrations, deployments or commercial release.

## Cross-repository automation
This package deliberately does not change the privileged registration dispatcher, QA #11/#12, or Development #81. After it passes independent QA review, propose a separately security-reviewed controller extension to route only the three registered plans, verify child runs and correlate exact SHA and request statuses. No new application PR may be marked QA PASS merely because this proposal exists.

## Reconciliation with QA PR #17

PR #18 is the preferred single implementation. Its billing browser suite includes the negative amount input case formerly unique to PR #17: negative rupee input must be rejected and must not create a fictional invoice. The new COMM-V1 independent browser suite therefore contains **10 feature cases** (consultation 3, Smart Rx 3, billing 4). A separate network refusal test runs with every plan. QA PR #17 must not be merged alongside this PR because of conflicting workflow and test paths.

**Security review and exact-source test execution remain pending.** Plan/schema lint alone is not acceptance evidence for the new feature previews.
