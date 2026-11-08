# AroNexa QA governance

**Single-source test repo, controlled agents**
1. AroNexa main development branch is protected; this QA repository cannot merge, deploy, or edit it.
2. Only one integration QA owner/task edits the common `tests/verified/` suite at a time, even if many feature agents generate proposed tests. Each agent proposes a PR to QA repository and must declare affected requirement IDs.
3. QA PR quality gate: test discovery, no live endpoints, actual successful browser/model rerun, full report+SHA evidence, non-overlapping edits, independent review.
4. No self-service rewrite of historical evidence, never turn skips into passes; audit `evidence/` for historical counts separately from new executions.
5. Synthetic-only tests default; backend/Testcontainers or any privileged SQL needs an explicit isolated disposable authorization and a different workflow. No original Windows PostgreSQL or Flyway Apply.
6. Current integrated UX is a mock; success does not authorize PHI, production, main merge, customer acceptance or C2 API integration.
7. Version review outputs by app SHA, QA SHA, run URL, execution date and test-count breakdown. Only mark `READY_FOR_INTEGRATION_REVIEW` when current exact SHA has passing independent evidence.
8. Shared file conflicts are adjudicated by designated integrator; no parallel agent edits same paths and no automatic merge without owner review.

**Current INT-R1 baseline:** app `52809efbc077cd6abb6860d870cc487cc8eddc42` (PR #61 DRAFT), Reception PR #36 DRAFT. W3-E original migration HOLD remains.
