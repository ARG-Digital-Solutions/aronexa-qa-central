# P01-T07-INT-REG01 — successful controlled QA rerun

**Status:** VERIFIED CI PASS IN TEST-ONLY SCOPE / INDEPENDENT REVIEW AND RELEASE GATES PENDING  
**Run:** https://github.com/ARG-Digital-Solutions/aronexa-qa-central/actions/runs/42585442420  
**Run ID:** 42585442420  
**Execution:** 2026-11-09 UTC, completed 08:24:38  
**QA Central workflow SHA:** `b6854a29762281b531f8b93e10cd54627300fd5d`  
**Backend PR #64 tested exact SHA:** `7f1fb76ce80a9fb838df06fc616e14f169bc2dd4`  
**Read-only frozen frontend PR #61 SHA:** `52809efbc077cd6abb6860d870cc487cc8eddc42`

## Verified job results

| Job | Conclusion | Evidence |
|---|---|---|
| Approved source SHA and disposable-only gate | PASS | Job 129054043939 |
| Backend complete `mvn -B -f backend/pom.xml verify` | PASS | Job 129054078792, `BUILD SUCCESS` |
| Frozen frontend build and independent Playwright | PASS | Job 129054078679 |

The backend CI explicitly checked out SHA `7f1fb76...`, verified the four-path scope against protected C2 base, and executed Maven verify on a Docker-enabled GitHub-hosted runner with fresh Testcontainers (no original Windows database).

**Maven totals:** **157 tests; 0 failures; 0 errors; 0 skipped.**

Targeted backend class evidence from Maven logs:

| Class | Passed | Failed | Errors | Skipped |
|---|---:|---:|---:|---:|
| `SyntheticRegistrationFrontendContractTests` | 5 | 0 | 0 | 0 |
| `SyntheticRegistrationHttpAcceptanceTests` | 18 | 0 | 0 | 0 |
| `SyntheticRegistrationIntegrationTests` | 35 | 0 | 0 | 0 |
| `PostgresTenantRlsTests` | 8 | 0 | 0 | 0 |
| `PatientRuntimeBoundaryTests` | 5 | 0 | 0 | 0 |
| `SyntheticPostgresLogRedactionAcceptanceTests` | 1 | 0 | 0 | 0 |

Additional backend classes comprise the remaining passing tests. The previously failed checked-exception test compilation issue is resolved in this exact run.

**Frontend:** successful build, **26/26** Reception model, **20/20** Appointments model, **8/8** verified Chromium Playwright, zero model failures/skips.

**Artifacts:** `int-reg01-backend-42585442420` and `int-reg01-frontend-42585442420`; both confirmed present in GitHub Actions.

## Evidence limitations and remaining release blockers

- This result is an **isolated synthetic/test-profile integration** PASS; it does **not** mean the actual frozen browser UI is connected to the C2 API.
- The run did not independently establish a full dependency vulnerability audit, external security penetration testing, human NVDA accessibility sign-off or customer acceptance.
- Secure duplicate-candidate retrieval, phone consent/persistence, authenticated frontend branch/session binding and production idempotency lifecycle remain unimplemented.
- Product V10 migration remains test-resource-only; no original/shared database or production deployment permitted.
- Independent reviewer approval and explicit owner merge/release authorization remain outstanding.
- QA Central PR #7 (runner pin + evidence) and product PR #64 remain separate review gates. No implicit merge.

**Disposition:** CONTRACT_TESTS_PASS / FULL_SOURCE_REGRESSION_PASS / FROZEN_FRONTEND_SYNTHETIC_PASS / INTEGRATION_ACTIVATION_NOT_READY.
