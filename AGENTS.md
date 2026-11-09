# AroNexa QA Central — agent operating rules

Scope: independent QA repository. This file applies only after this reviewed PR is merged. Product Master Engineering Contract V3.0 remains authoritative for engineering scope.

1. All new AroNexa QA planning, browser/API/security/accessibility test harnesses, evidence and independent QA decisions live here. Tests that must compile beside application source remain in the product repository, but are orchestrated and evidenced from here.
2. Start every new QA task by inspecting the current approved `qa/plans/<PLAN_ID>.json`, source product PR and current exact SHA, relevant requirement IDs, approved source scopes and dependency holds. Unknown plan IDs **fail closed**; never guess an alternative test suite.
3. Do not reuse the P01-T07-INT-REG-01 synthetic suite as evidence for unrelated new modules. Extend the approved plan registry and workflow allowlist through a separate draft QA PR and independent review.
4. QA test workflows use synthetic fixtures only, fresh disposable Testcontainers when backend SQL is needed, localhost browser tests and ephemeral GitHub-hosted runners. Never access original Windows/shared/production databases, real patient data, PHI, production APIs or secrets in logs/screenshots/artifacts.
5. Version every result by exact application SHA, QA workflow SHA, plan ID, run/request ID, job conclusions, executed test counts, failures/skips and CI artifacts. Missing/skipped/stale/unauthorized test results never count as PASS.
6. Cross-repo dispatch validates same-repo application PR ownership, current SHA, base, label and reviewed plan on the default QA branch. Only allowlisted workflows may run.
7. Privileged product commit-status publishing belongs only in the isolated QA reporter job; never pass reporting tokens into app source checkouts, Maven, npm or browser tests. Never change workflow permissions or trusted event type silently.
8. Post an exact-SHA PR status and issue receipt only after required testing. A PASS approves **test-only automated QA**, not independent security review, customer acceptance, product merge, database migration, deployment or new development scope.
9. QA agents can record defects and propose test fixes on isolated branches; they cannot modify protected application source/PRs. Development agents reference QA results but still need owner approval for new scope.
10. No self-approval. Keep PRs draft until independently reviewed; document all failure and rerun evidence, never rewrite prior results to say they passed.
11. For setup and trigger instructions read `docs/AUTO_QA_01_CROSS_REPO_SETUP.md`. Codex reading this file does not automatically schedule or spawn agents.
