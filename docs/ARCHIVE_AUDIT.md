# Source archive audit — 2026-11-09

All input archives were **read without executing their scripts**. `.git` internals, node_modules, generated build jars/classes, and source app runtime were excluded from the QA repository. Original ZIPs were left unchanged.

| Source | Findings | Central QA treatment |
|---|---|---|
| `Testing Suite AroNexa.zip` | 8 Playwright `.spec.mjs` files, 2 helper scripts, config and package; archived JUnit **69 total / 69 skipped / 0 passed** | Preserve exact tests and support in `legacy/`; current verified suites in `tests/verified/` |
| `AroNexa-C2-Test.zip` | **18** Java JUnit test classes and archive with **133 passed / 0 failures / 0 errors / 0 skipped** | Preserve class-level summarized evidence; backend JUnit continues to run from product repository's exact source SHA, not copied into QA |
| `AroNexa-INT-R1-Review.zip` | Integrated React/Vite frontend and Reception + Appointment model test files | Preserve model test reference copies; QA runner invokes active product tests from pinned app checkout |
| `AeroNexa Feature Testing 06-Nov.zip` | No usable test source | No import |
| `AroNexa-Codex-Worktrees.zip` | Four development worktrees. Agent 02 Reception model test semantically matches INT-R1; Agent 04 Appointment test differs only by line endings, not test content | No duplicated tests or worktree source imported |
| `codex.zip` | Agent prompt starters, review reports, UI patches; no runnable QA suite | Recorded as provenance only; do not mix prompts or patches with tests |
| Duplicate `(1).zip` archives | Exact same SHA256 as corresponding Codex archives | Deduplicated |

### C2 JUnit class-level evidence (archived snapshot)

| Class | Tests | Failures | Errors | Skipped |
|---|---:|---:|---:|---:|
| `ArchitectureTests` | 1 | 0 | 0 | 0 |
| `AronexaApplicationTests` | 7 | 0 | 0 | 0 |
| `AuthRoleBoundaryTests` | 4 | 0 | 0 | 0 |
| `AuthenticationIntegrationTests` | 12 | 0 | 0 | 0 |
| `OrganizationAccessIntegrationTests` | 7 | 0 | 0 | 0 |
| `PostgresTenantRlsTests` | 8 | 0 | 0 | 0 |
| `TenantAuthorizationTests` | 8 | 0 | 0 | 0 |
| `ModuleAccessServiceTests` | 5 | 0 | 0 | 0 |
| `ModuleRegistryPostgresTests` | 6 | 0 | 0 | 0 |
| `OrganizationPersistenceTests` | 9 | 0 | 0 | 0 |
| `PatientAccessServiceIntegrationTests` | 6 | 0 | 0 | 0 |
| `PatientIdentitySchemaTests` | 5 | 0 | 0 | 0 |
| `PatientRegistrationRulesTests` | 7 | 0 | 0 | 0 |
| `PatientRuntimeBoundaryTests` | 5 | 0 | 0 | 0 |
| `SyntheticRegistrationAttemptLimiterTests` | 5 | 0 | 0 | 0 |
| `SyntheticRegistrationHttpAcceptanceTests` | 8 | 0 | 0 | 0 |
| `SyntheticRegistrationIntegrationTests` | 27 | 0 | 0 | 0 |
| `SyntheticRegistrationProofTests` | 3 | 0 | 0 | 0 |

**Evidence integrity:** 
- Archived JUnit passing results are historical, not an independent successful rerun on latest source.
- Archived Playwright JUnit has **zero passing tests** because its 69 testcases were skipped; it must not be called green acceptance.
- Earlier operator-reported **21/21** local browser passes are an owner report, **not proven by the uploaded XML**. Obtain export of the actual passing JUnit/HTML report before accepting as reproducible evidence.
- The main existing tests were not rewritten: legacy source remains available to adapt incrementally, under review.
- No patient data, database credentials, Docker volumes or machine-specific archives are committed.
