# QA38 WIN11P Reception infrastructure proposal
Status: DRAFT_NOT_ACTIVATED. WIN-11B and customer release remain NOT_READY.
This document supersedes the infrastructure-absent portions of the earlier PR37 review report; it does not supersede missing real execution or independent review.

## Design and boundaries
The existing INT-REG01 controller and workflow are unchanged Git blobs. The plan validator routes only the exact WIN11P plan/workflow pair to a separate strict contract; unknown plans/pairs fail. All eight original WIN11P checks remain required. A successful schema lint means structurally valid, not reviewed or activated.

The new qa-win11p-reception.yml has only workflow_dispatch. It rejects non-main refs, another QA repository, an unacknowledged run, an unapproved exact QA revision, an unapproved runner, stale/forked/wrong-base source, changed source scope, and absent/currently rejected independent code review. It requires current open draft PR148 HEAD and exact reviewed plan pins; no product label, ready-for-review transition or automatic-dispatch change is needed. Existing automatic draft deferral remains intact.

Three jobs form the trust boundary:
1. A GitHub-hosted prepare job checks trusted QA code, current product PR metadata, independent PR37 review and all 13 exact source paths. It executes no app code. Source is transported as a Git bundle with no stored credentials; trusted QA code is a Git archive. SHA256 hashes and a current-run context digest anchor both.
2. A proposed one-job Windows VM receives no source-read/status-write secret, does not checkout through an authenticated action, verifies all input hashes before loading the runner, and executes the reviewed source only in a new private directory. It requires Java21, Node24, Maven, Python, PowerShell, Playwright and a fresh isolated Linux-container Docker engine. Existing containers, operator labs, ports5176/5186 and inherited DB/JVM/Node overrides cause refusal. No recursive host cleanup or enrollment is performed.
3. A separate GitHub-hosted reporter never checks out or executes product code. It validates the actual artifact API identity, exact QA/run/name/digest and downloaded ZIP bytes; only evidence.json is accepted. It rechecks the live source head, QA approval/admin pin, all counts/gates and independent artifact-bound operator/reviewer receipts before preparing a status. Only its final step references the product status-write credential.

Execution artifacts are untrusted inputs. The collector reduces private logs/XML to an exact allowlist of identity hashes, numeric counts, versions, PIDs, marker UUIDs and gate outcomes. The reporter rejects arbitrary fields, raw text, additional ZIP entries, stale runs, changed hashes, failed/skipped/empty required tests and missing human disposition. It never runs downloaded scripts. This constrains the status trust boundary; it does not make source-authored tests immune to dishonest implementation. Independent review of the pinned source and human run evidence remains necessary.

## Eight retained checks and execution evidence
| Original required check | Evidence and refusal conditions |
|---|---|
| exact_source_sha_and_clean_checkout | Current draft PR148 head, exact base/branch, ancestor baseline, 13-path set, credential-free Git bundle SHA256, clean tracked source after execution |
| portable_java21_actual_forked_jvm_identity | Fresh jlink ALL-MODULE-PATH runtime; both actual phase XML java.home paths and java.version21; runtime file-inventory SHA256 unchanged |
| frontend_model_regression_and_connected_build | Locked npm install, Node24, all frontend tests (minimum249; no failures/skips/cancellation), connected TypeScript/Vite build |
| real_http_pg17_tenant_branch_staff_session_rls_negatives | Search-security minimum7, AuthRoleBoundary minimum4 and PostgresTenantRls minimum8, all JUnit cases/counters verified |
| chromium_login_search_registration_booking_checkin_daily_queue | Existing RC03 Phase A; all source assertions retained; one expected JUnit method and source marker summary |
| same_marked_database_distinct_backend_process_restart | Existing RC03 Phase B, different positive PIDs, same fresh run marker, source runner PASS_B verification; PostgreSQL server major17 observed through exact labelled/name/loopback/marker checks |
| operator_workflow_on_connected_frontend | New Pilot09 session in dedicated VM console, one expected JUnit method, nonzero patient and check-in counts, separate observed PG17 marker; artifact-bound human operator and reviewer receipts |
| full_maven_failures_preserved | Actual mvn verify result and every JUnit testcase/count preserved as sanitized totals. Any failure/error/skip or missing reports blocks a positive status. No blanket acknowledgement or package-only bypass |

Automated RC03 restart and the later operator lab intentionally use different marked disposable databases. Neither is an installed normal-JAR clinic service or production-functionality proof. The source operator lab may expire after45 minutes; an empty/untouched lab fails. It does not establish clinical UAT.

Raw Surefire, Maven, browser and operator logs/staff sheets remain private on the disposable VM. They may contain generated development credentials. Only normalized evidence.json is uploaded. Input source artifacts expire after1 day; normalized execution evidence after14 days. Administrator must guarantee VM/engine destruction after one job, including cancellation/failure. This proposal does not enroll a VM, expose RDP or create a Docker endpoint.

## Explicit owner/admin decisions required before activation
- Independent human review of the exact PR37 code and current pinned product source. Implementation author cannot supply approval or operator/reviewer receipts. Assign real GitHub reviewer and operator identities.
- Approve a policy exception to the current GitHub-hosted-only QA rule for a dedicated **ephemeral one-job interactive Windows VM** with isolated Linux Docker. The label aronexa-win11p-ephemeral and actionlint label declaration do not enroll or authorize any machine. Never label the owner's working PC or attach to an active QA session.
- Preprovision tools above and fresh engine, a dedicated interactive operator console, no clinic DB routes/mounts/secrets, no previous job work directories. Administrator controls VM creation/destruction and enrollment; runner must use GitHub's ephemeral one-job registration. None is configured by these scripts.
- Configure protected environments win11p-control-approval, win11p-disposable-execution and win11p-independent-report, with independently assigned reviewers, prevent-self-review and appropriate main-branch restrictions. Confirm platform support and bypass policy; do not assume a newly referenced environment has protection.
- Separately authorize any reviewed default-branch publication/merge. This task prohibits merge; no workflow can be dispatched from this draft branch because the manual control requires trusted main.
- Set configuration only after review: WIN11P_AUTHORIZED_QA_SHA=the exact authorized main QA commit; WIN11P_REVIEWED_QA_SHA=the independently approved PR37 revision; WIN11P_WINDOWS_RUNNER_APPROVED=true; WIN11P_REVIEWER_LOGIN and WIN11P_OPERATOR_LOGIN. Control and report must see identical protected values. The code compares all execution inputs between reviewed and actual QA commits, allowing only non-executable documentation drift.
- Revalidate current PR148 head against the plan. Do not substitute owner-local bce7a9d for current head89c985d, or silently update a moving source pin. Re-review plan changes before a new run.

## Permission requirements (proposal; no credentials changed)
| Boundary | Required access | Excluded |
|---|---|---|
| Prepare GitHub token | QA Contents read, Pull requests read | Product writes, app execution |
| ARONEXA_SOURCE_READ_TOKEN in prepare/report only | Selected product repo Contents read for checkout and Pull requests read for private PR metadata | Product source/status writes |
| Windows execute | Default QA Contents read plus temporary Actions artifact transport; no product secrets referenced/exported | Source-read token, product status token, private clinic credentials |
| Reporter GitHub token | QA Contents read, Pull requests read, Actions read, Issues write for issue38 receipt | App execution/product writes |
| ARONEXA_DEV_STATUS_TOKEN in reporter final step only | Selected product repo Commit statuses write; metadata read | Contents write, merge/deploy |

GitHub documents [read permission for private PR metadata](https://docs.github.com/en/rest/pulls/pulls#get-a-pull-request) and [Actions read plus artifact digest/provenance metadata](https://docs.github.com/en/rest/actions/artifacts#get-an-artifact). Existing secret names alone do not establish their effective scopes or validity. Owner/admin must verify or separately authorize credential changes; this task neither reads values nor alters scopes. Protected environment secrets are preferable for reporting; any move/configuration is a separate admin action.

## Run and disposition procedure (future review only; do not execute now)
1. After all review/admin decisions and separately authorized trusted-main publication, an authorized maintainer manually dispatches qa-win11p-reception.yml with exact plan HEAD source_sha and acknowledge_disposable_only=true. No repository_dispatch permission or product draft policy changes.
2. Approve the control environment only for this exact QA/source/request. Execution is scheduled solely on the enrolled one-job Windows VM.
3. The independent operator uses the dedicated VM console, localhost5176 operator lab and source-created private staff sheet. Create only fictional records, search/register/review duplicate rejection/book/check in/inspect queue, then create the source STOP file. Do not upload staff sheets or screenshots with identifying content.
4. Inspect normalized artifact and all required job outcomes. Compute SHA256 of the evidence.json bytes and record current artifact ID, source SHA, QA SHA, request ID, run ID/attempt. Both the configured operator and independent reviewer post their own direct JSON disposition in QA issue38.
5. Only after genuine execution/review may each human change this **NOT_RUN template** to PASS and confirm the operator workflow:
~~~json
{
  "plan_id":"WIN11P_RECEPTION_E2E",
  "source_sha":"<exact source SHA>",
  "qa_sha":"<exact QA SHA>",
  "request_id":"<run_id>-<run_attempt>",
  "run_id":"<run_id>",
  "run_attempt":"<run_attempt>",
  "artifact_id":0,
  "evidence_sha256":"<SHA256 of evidence.json bytes>",
  "disposition":"NOT_RUN",
  "operator_workflow_confirmed":false
}
~~~
The configured human authors must differ from the product/QA implementation authors. Latest matching receipt controls; a later FAIL cannot reuse an older PASS. No bot or source-authored evidence can independently approve this. The two configured roles may only coincide if independently approved by the owner/review process.
6. Approve the independent-report environment after checking artifacts and receipts. Reporter revalidates current source/review/configuration, ZIP digest and exact all-gates evidence. Only then can its isolated status step run. Missing/failed jobs, operator evidence, full-Maven success, artifact or receipt yields no positive status.
7. Verify aronexa/central-qa/WIN11P_RECEPTION_E2E on the exact current head, unique request, linked run, QA SHA, counts and reviewer disposition before any gated product work. A green infrastructure-lint job is not this status.

## Review checklist
- [ ] Legacy controller and workflow Git blob pins unchanged; old plan gates preserved.
- [ ] Exactly eight original WIN gates; no empty/skipped/failing check can report positive.
- [ ] Manual only; main/QA repository/exact admin SHA/PR head/base/scope and independent approval all enforced.
- [ ] Windows VM policy exception, topology, lifecycle/destruction, console and enrollment independently approved.
- [ ] No product credentials on execute; source Git bundle has no credentials; hashes verified before script load.
- [ ] Portable phase JVM homes AND Java21 versions verified; runtime inventory unchanged.
- [ ] Observer never touches unlabelled/non-loopback databases; actual PG17 marker observations bind both distinct lab runs.
- [ ] XML counters agree with testcase children; full Maven failures retained and blocking; operator lab nonempty.
- [ ] Reporter accepts only current-run exact ZIP artifact and independent latest receipts; never executes artifact content.
- [ ] Real exact-head Windows execution remains NOT_RUN until recorded. Full-Maven source failures may require separately authorized product corrections.
- [ ] No original DB, merge, deploy, protected-setting activation, Central PASS or customer-readiness claim in this preparation task.
