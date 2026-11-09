# P01-T07-INT-REG-01 — QA Central test plan

**Central QA status:** TEST PLAN PREPARED / NOT_RUN / NOT_RELEASE_READY  
**Product PR:** https://github.com/ARG-Digital-Solutions/aronexa-healthcare-platform/pull/64  
**Backend exact head:** `8788b89ddceb70c085818939a82c3476887006bd` (verify before run)  
**Frozen frontend exact head:** `52809efbc077cd6abb6860d870cc487cc8eddc42`  
**Backend C2 baseline:** `cfdb03c631c2ed6df687b71d68fcc890a1eb9cc4`

## Centralized execution

Workflow: `.github/workflows/qa-int-reg01.yml` (pending QA PR review/merge; workflow_dispatch only).

Once this QA workflow has been independently approved and merged into QA Central `main`, an authorized maintainer can run:

```powershell
gh workflow run qa-int-reg01.yml `
  --repo ARG-Digital-Solutions/aronexa-qa-central `
  -f backend_sha=8788b89ddceb70c085818939a82c3476887006bd `
  -f frontend_sha=52809efbc077cd6abb6860d870cc487cc8eddc42 `
  -f acknowledge_disposable_only=true

gh run list --repo ARG-Digital-Solutions/aronexa-qa-central `
  --workflow qa-int-reg01.yml --limit 5
```

Review run URL, **both job conclusions**, JUnit/Playwright artifacts, failure logs and exact app+QA SHA. Do not claim PASS solely because workflow dispatch was accepted.

## Gates and evidence register

| Gate | Source of executable test | Status before run |
|---|---|---|
| Versioned mapping `FULL→EXACT`, `UNKNOWN→null` | Product `SyntheticRegistrationFrontendContractTests` | NOT_RUN |
| Nonempty unsupported phone is blocked | Same test-only adapter | NOT_RUN |
| Authenticated 201 and identical-key 200 receipt | Product HTTP contract test | NOT_RUN |
| Changed-payload replay 409 / duplicate review 409 / no auto-merge | Product HTTP/SQL regression | NOT_RUN |
| Missing bearer, wrong branch, missing permission, tenant isolation | Product HTTP/SQL tests | NOT_RUN |
| Session expiration/revocation, module authorization | Existing C2 regression | NOT_RUN |
| Concurrency and idempotency under contention | Existing C2 IntegrationTests | NOT_RUN |
| SQL RLS, least privilege, signing-proof resistance | Existing C2 IntegrationTests | NOT_RUN |
| Malformed requests, request size, rate limiting, safe logs | Existing C2 HttpAcceptanceTests | NOT_RUN |
| Full Maven verify on ephemeral PostgreSQL | QA Central `backend-disposable` | NOT_RUN |
| Frozen PR #61 TypeScript/Vite and model tests | QA Central `frozen-frontend` | NOT_RUN |
| Verified Reception/Appointment Playwright | QA Central `tests/verified/` | NOT_RUN |
| SAST / SBOM vulnerabilities / independent security reviewer | Separate audited security gate and reviewer | NOT_RUN |

## Expected evidence and acceptance

A run is eligible for **QA review only** if the backend and frontend jobs each complete successfully on exact approved product SHAs, source scope check passes, Testcontainers actually executes, all relevant tests pass without skips hiding failures, artifacts are present, no sensitive data leaks, and any security/SAST exclusions are independently reviewed. This is not a customer-release gate. A missing job/artifact is BLOCKED/INCONCLUSIVE, not PASS.

## Recorded unresolved gaps

- Phone persistence, consent and verified duplicate-candidate retrieval are not implemented.
- Frozen frontend not connected to live registration API, server identity/branch/session, or idempotency lifecycle.
- Proposed test-resource V10 is NOT an authorized production migration.
- Manual NVDA, broader security review, release approval remain separate.
- No original Windows/shared development DB access, PR merge or deployment is permitted.

## Follow-up after an actual run

Update this report or a new dated evidence file under `evidence/int-reg01/` with exact GitHub Actions run URL, app SHA, QA SHA, test counts, failed/skipped cases, independent reviewer, and PASS/FAIL/BLOCKED disposition. Leave archived evidence files unchanged.


## Central QA PowerShell launcher (after workflow review and merge)

The original local `run_p01_t07_int_reg01_ci.ps1` targets the **product** repository's `pr-quality.yml` and is not the central execution path. The reviewed QA Central equivalent is `scripts/Run-P01-T07-INT-REG01-CentralQA.ps1`. It validates the pinned product branch head and frontend SHA, verifies the QA workflow exists on `main`, triggers `qa-int-reg01.yml`, watches its jobs and emits local `artifacts/int-reg01/P01_T07_INT_REG01_QA_EVIDENCE.json` in a QA Central checkout. It uses GitHub CLI and no local database or local Maven/Docker.

```powershell
Set-Location 'C:\Users\ganes\Application Development\AroNexa-QA-Central'
git pull origin main
& .\scripts\Run-P01-T07-INT-REG01-CentralQA.ps1
```

**Only run after QA PR #5 has been independently reviewed and authorized for merge to main.** Never treat the generated JSON summary as a substitute for logs, JUnit, Playwright reports or independent security review. PowerShell launcher execution has **not** yet been validated in Windows.
