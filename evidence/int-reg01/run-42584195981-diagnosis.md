# P01-T07-INT-REG01 — Execution 42584195981 (failure and remediation)

**Execution:** 2026-11-09 UTC  
**GitHub Actions:** https://github.com/ARG-Digital-Solutions/aronexa-qa-central/actions/runs/42584195981  
**QA workflow main SHA:** `b6854a29762281b531f8b93e10cd54627300fd5d`  
**Product input SHA (failed compile):** `8788b89ddceb70c085818939a82c3476887006bd`  
**Frozen frontend SHA:** `52809efbc077cd6abb6860d870cc487cc8eddc42`

## Actual job results

| Job | Status | Verified evidence |
|---|---|---|
| Approved source pin and disposable-only gate | PASS | CI job 129049956986 |
| Backend Maven + PostgreSQL | **FAIL at testCompile** | CI job 129049997508 |
| Frozen frontend | PASS | CI job 129049997571 |
| Reception Node model | PASS 26/26 | Frontend job console |
| Appointment Node model | PASS 20/20 | Frontend job console |
| Synthetic verified Playwright | PASS 8/8 | Frontend job console |

**Root cause:** Java compiler errors on two lines of source-coupled test class `backend/src/test/java/com/argdigital/aronexa/patient/SyntheticRegistrationFrontendContractTests.java`, line 207 and 212:

```
unreported exception java.lang.Exception; must be caught or declared to be thrown
```

Method `versionedContractDocumentsExplicitFrontendMappingAndNoLiveActivation` had two `mappedFrontendBody(...)` calls but did not declare checked exceptions. No backend integration or PostgreSQL contract tests ran because compilation failed before test execution. This is **not evidence of a product registration runtime defect**.

**Authorized source-only fix:** Product branch `codex/p01-t07-int-reg01-contract-20261109`, commit `7f1fb76ce80a9fb838df06fc616e14f169bc2dd4`: add `throws Exception` to that test method declaration. This stays within the four originally approved product paths. **Fix is committed, but compilation on the new SHA is NOT RUN.**

## Rerun procedure (manual QA Central workflow dispatch; not in product repo)

The centrally managed `qa-int-reg01.yml` workflow is active on `main`. An authorized operator can trigger it directly, even before a local PowerShell launcher pin update is reviewed:

```powershell
gh workflow run qa-int-reg01.yml `
  --repo ARG-Digital-Solutions/aronexa-qa-central `
  --ref main `
  -f backend_sha=7f1fb76ce80a9fb838df06fc616e14f169bc2dd4 `
  -f frontend_sha=52809efbc077cd6abb6860d870cc487cc8eddc42 `
  -f acknowledge_disposable_only=true
```

Then inspect exact run head/inputs, backend Maven result, JUnit/SQL evidence and browser artifacts. Do not merge product PR #64 or claim readiness until full backend tests and independent security review pass. The QA runner's pinned SHA change is staged in QA branch `qa/int-reg01-retest-pin-20261109` and requires standard QA review before merging.

**Disposition:** `FAIL_COMPILE` for run 42584195981; `NOT_RUN` for new product SHA; `NOT_READY` for release.
