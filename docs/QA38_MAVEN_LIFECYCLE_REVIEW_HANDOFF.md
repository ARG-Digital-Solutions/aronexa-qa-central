# QA38 Maven lifecycle correction: independent review proposal

Status: **DRAFT_NOT_ACTIVATED / NOT_READY / rule 27 HOLD**. This is review preparation only. No execution approval, reviewer disposition, operator receipt, runner enrollment, credential change, merge or deployment is recorded.

## Source and scope decisions to review

Live product PR148 is draft at **065cfea959bfe6fd1ad334a7ccae98f84a1ddf9a**, base `codex/win11p-integrated-reception-e2e` at `1abb41ba76acef072001336d8b86d4a0d29ac6a2`. Local preliminary code was tested at **ce7fbbc0b7d6658e5c4f9a252dec98dfa5df5ef5**. The five intervening changed paths are documentation/sanitized JSON only, enumerated in the review manifest. This is not an exact-head execution waiver. Repeat live head/base/draft checks immediately before any independent run and reporting; source drift invalidates this proposal.

QA PR37 started this preparation at **b561aa3b6710319dc6d41d597791281805b0ee64**. Its earlier CI checkpoint `713e0526cfa0d9d5fff80d7d71f1a545a59cf43d` proves infrastructure checks only. It does not prove acceptance at this new product head or approve the new QA revision.

Changed files in this QA preparation:

| Path | Change |
|---|---|
| `qa/plans/WIN11P_RECEPTION_E2E.json` | Refresh current source/frontend pins to 065cfea; reference pending review proposal and blockers. Preserve prior 13-path allowlist, all eight checks, NOT_RUN and DRAFT_NOT_ACTIVATED. |
| `qa/reviews/QA38_MAVEN_LIFECYCLE_REVIEW.json` | Candidate 26-path manifest with Git blob identities, old/new scope reconciliation, exact local evidence references/digests, proposed lanes, inventory and normalized mapping. No execution authorization. |
| `docs/QA38_MAVEN_LIFECYCLE_REVIEW_HANDOFF.md` | This review package, provisioning/teardown design, gate mapping, approvals, checkpoint and validation record. |
| `docs/QA38_INDEPENDENT_REVIEW_AUTHORIZATION_HANDOFF.md` | Add a current review-preparation notice; retain earlier historical handoff. |

No workflow, controller, executor, collector, reporter, product file or INT-REG01 plan changed. Existing QA worktree and its untracked caches are preserved; product worktrees/output and port5176 are untouched.

The existing plan field `authorized_changed_paths` remains the original **13 paths**. The full **26-path** proposal has **13 retained paths and 13 proposed additions**. `Pilot05SeparateJvmHttpTests.java` is a retained path modified again by lifecycle tags; its new content needs review too. The manifest enumerates every path and exact head blob. There are no wildcard additions. **Current source-scope validation must reject the 26-path source.** New `review_preparation` metadata is informational, not a new runtime authorization mechanism. An independently reviewed, separately authorized follow-up must decide whether to promote the candidate scope into the execution allowlist.

## Reconciled source scope

The machine-readable manifest is authoritative for the proposed exact paths and blob identities. The following categories explain why each path is present; presence is not approval. Original 13 paths are the prior draft scope, not a claim that an independent reviewer already approved them.

| Path | Review status |
|---|---|
| `backend/pom.xml` | Proposed addition; not authorized |
| `backend/src/test/java/com/argdigital/aronexa/appointment/AppointmentCandidateHttpAcceptanceTests.java` | Proposed addition; not authorized |
| `backend/src/test/java/com/argdigital/aronexa/appointment/Pilot05SeparateJvmHttpTests.java` | Retained path; changed again, review required |
| `backend/src/test/java/com/argdigital/aronexa/appointment/Win11pTestInventoryTests.java` | Proposed addition; not authorized |
| `backend/src/test/java/com/argdigital/aronexa/patient/PatientCandidateSearchHttpAcceptanceTests.java` | Retained prior draft path |
| `docs/superpowers/plans/2026-11-15-win11p-maven-lifecycle.md` | Proposed addition; not authorized |
| `docs/windows/WIN11P_146_ALTERNATE_PORT_PROPOSAL_20261115.md` | Retained prior draft path |
| `docs/windows/WIN11P_146_FICTIONAL_DATA_ACCEPTANCE_20261115.md` | Retained prior draft path |
| `docs/windows/WIN11P_146_LOCAL_PREFLIGHT_20261115.md` | Retained prior draft path |
| `docs/windows/WIN11P_146_PORT5186_ACCEPTANCE_20261115.md` | Retained prior draft path |
| `docs/windows/WIN11P_MAVEN_TEST_LIFECYCLE_BUILD_LOG_20261115.md` | Proposed addition; not authorized |
| `docs/windows/win11p-maven-evidence/method-inventory-512c0d5fb9ecaed630a4642b80a76425d86f23b9.json` | Proposed addition; not authorized |
| `docs/windows/win11p-maven-evidence/method-inventory-ce7fbbc0b7d6658e5c4f9a252dec98dfa5df5ef5.json` | Proposed addition; not authorized |
| `docs/windows/win11p-maven-evidence/ordinary-matrix-results-512c0d5fb9ecaed630a4642b80a76425d86f23b9.json` | Proposed addition; not authorized |
| `docs/windows/win11p-maven-evidence/ordinary-matrix-results-ce7fbbc0b7d6658e5c4f9a252dec98dfa5df5ef5.json` | Proposed addition; not authorized |
| `frontend/test/browser/pilot06-preview-readiness.mjs` | Retained prior draft path |
| `frontend/test/browser/pilot08-rc03-created-restart.mjs` | Retained prior draft path |
| `frontend/test/browser/rc03-preview-port.ts` | Retained prior draft path |
| `frontend/test/patient-candidate-search-client.test.mjs` | Retained prior draft path |
| `frontend/test/rc03-preview-port.test.mjs` | Retained prior draft path |
| `frontend/vite.connected-reception.config.ts` | Retained prior draft path |
| `scripts/pilot/Invoke-Win11p-MavenMatrix.ps1` | Proposed addition; not authorized |
| `scripts/pilot/Test-AroNexa-Pilot05-DistinctJvm-Restart.ps1` | Retained prior draft path |
| `scripts/pilot/Test-Win11p-MavenMatrix.ps1` | Proposed addition; not authorized |
| `scripts/pilot/Win11p-MavenMatrix.psm1` | Proposed addition; not authorized |
| `scripts/pilot/win11p-maven-matrix.json` | Proposed addition; not authorized |

## Preliminary local evidence, with provenance limits

At tested code `ce7fbbc0...`: **343 ordinary PASS + 1 discovery PASS + 14 focused checks reported PASS; 0 failures/errors/skips; 8 guarded methods NOT_RUN**. Inventory contains **352 method IDs** (343 ordinary, 1 discovery, 8 guarded). Coordinator **exit2 / NOT_PASS**, `full_verification=NOT_PASS`, `central_qa=NOT_RUN`. Run `78c2bb77f4b24bf4ae6766033ef4a891`; PowerShell child PIDs **13488 / 41248** are discovery/ordinary orchestration processes, not phase A/B JVM identities. There is no current-head independent run, request or reviewer disposition.

Artifact references in `qa/reviews/QA38_MAVEN_LIFECYCLE_REVIEW.json` pin the product Git blobs, raw Git-content SHA256 and byte lengths. Read with `git show <source-head>:<path>`; working-tree CRLF conversion can change file-byte hashes. The method inventory and matrix JSON are local reference evidence; do not feed them to the privileged reporter as current independent evidence. The 14-check result is documented in the product build log; no committed standalone machine result for those checks was supplied. Earlier `512c0d5...` JSON files and bce7a9d Reception results are historical and excluded from this checkpoint's execution results.

## Proposed Maven lane selection

These are proposed selections for an amended executor, not changes to the current executor. Every source method remains mandatory. Default product Maven is still unfiltered.

| Lane | Selection | Expected method count | Prerequisites / evidence |
|---|---|---:|---|
| Discovery | `-Pwin11p-discovery ... test` | 1 | Fresh exact-head checkout; inventory SHA must equal current source. |
| Ordinary | `-Pwin11p-ordinary ... verify` | 343 | Disposable Testcontainers PG17; all unit/integration/security/architecture tests; no Pilot acknowledgements. |
| Pilot05 legacy A, B | `-Pwin11p-method`, tags `win11p-pilot05-phase-a`, `win11p-pilot05-phase-b` | 1 each | Same newly marked DB per pair; separate JVMs; B validates committed A records. |
| Pilot05 RC03 A, B | tags `win11p-pilot05-rc03-phase-a`, `win11p-pilot05-rc03-phase-b` | 1 each | A browser creates patient/booking/check-in; B recovers same records; connected build, Playwright and portable-JVM evidence; approved RC035186. |
| Pilot06 connected browser | tag `win11p-pilot06-browser` | 1 | Genuine synthetic-runner authorization, QA Playwright installation and required free localhost port in the disposable VM. |
| Pilot07 disposable restore | tag `win11p-pilot07-recovery` | 1 | Genuine recovery acknowledgement; its own disposable PG17. **Unencrypted restore only**. |
| Pilot07 interactive operator | tag `win11p-pilot07-operator` | 1 | Real human acknowledgement, dedicated lab folder/marker, connected build and nonempty human observations/receipt. |
| Pilot09 operator (discovered guard) | tag `win11p-pilot09-operator` | 1 | Separate newly marked operator DB and lab; real independent human workflow; not a substitute for Pilot07. |

Every guarded tag must match the exact method ID in the manifest. Reconcile discovery's complete method-ID set against executed XML cases. Require exactly one PASS per method in its declared lane. Reject missing, duplicate, unexpected, failed, errored and skipped results. Counts are exact pins for this source, not permission to force success if discovery changes. Nested/inherited/parameterized tests need explicit discovery review if introduced.

Security `search/roles/rls`, RC03 `phase_a/phase_b` and Pilot09 `operator` remain separate proof projections for the existing gates, but their method results must contribute **once** to the 352-method matrix. Do not rerun wrappers and add duplicate phase results to a total; do not add security subsets to343. The 14 focused PowerShell checks and frontend cases are separate from the352 JUnit methods. The actual current coordinator orders guarded methods by discovered ID; its sequence differs from this conceptual table. Review dependencies, DB lifetimes and port occupancy against that actual ordering before adapting execution.

The current Central executor still runs plain `mvn verify`, then separate security/RC03/operator wrappers. It has not been adapted here. The product coordinator's `All` path has not had real execution; it requires externally provisioned phase databases and a supplied authorization JSON/digest. That JSON validates declared metadata, not GitHub review authenticity. Only the existing protected control-plane review and administrator process can authorize execution.

## Missing provisioning and safe teardown contract

Required future provisioning design, to be implemented/tested only under separate authorization:

1. Start on a dedicated one-job Windows VM with an empty isolated Linux Docker engine. No reuse of an existing workstation/QA session, original database or shared Docker volume. The reviewed image selection must retain PG17; record the resolved image identity. Java21, Node24, Playwright and the exact QA/source transport identities must be observed, not inferred from configuration.
2. Provision a fresh database/container for each legacy pair, RC03 pair and Pilot09 operator session. Keep each A/B pair's exact container alive until B and evidence capture finish. The existing Pilot05 runner provisions and tears down a complete pair internally; it cannot be used as a provision-only service without an approved orchestration change. The coordinator has no provisioning/cleanup owner today.
3. Match the existing Pilot05 contract: unique UUID and `com.argdigital.aronexa.pilot05.run` label, matching container name/full ID, single random loopback binding, database `aronexa_pilot05_disposable_only`, application of the existing test-role bootstrap, and pre-Spring `qa_guard.pilot05_run_marker` with matching run/database. Verify PG major17 and readiness using only the owned container. Do not use a guessed URL or fabricate a preexisting marker. Preserve nonowner/RLS/role assertions and migration guards. Do not grant BYPASSRLS to make tests pass.
4. Pass each lane's consent/phase settings only to its authorized child. No user/machine/global acknowledgements, inherited datasource overrides or reporter/source-read credentials in untrusted execution. Real operator acknowledgement and independent artifact-bound receipts are distinct; no generated JSON or marker is a human receipt.
5. Keep the 5176 default and approved RC035186 alternate. Pilot06/operator port contracts require their own free ports in the new VM; do not switch them silently, terminate an existing listener, change Windows permissions or touch the owner's5176 session. Stop the affected lane if a required port is occupied.
6. Capture per-lane immutable reports, exact method results, actual Java PIDs/home/version/runtime digest, source/QA/request/run IDs and marker-scoped DB observations before cleanup. Verify distinct A/B Java PIDs, same marker and persisted records; orchestration PIDs cannot substitute. Keep context-only duplicate proof reports outside the unique execution total.
7. In success, failure, cancellation and timeout paths, stop only processes created by this request after verifying their identity and lineage; inspect the exact owned full container ID, name and label immediately before stopping/removing it. Do not use broad `Stop-Process`, Docker prune, name-only deletion or recursive deletion of computed unverified paths. A missing/mismatched identity must refuse destructive cleanup, mark teardown incomplete and require VM destruction; it must never authorize touching another session.
8. Preserve failed-lane evidence before teardown. Do not rerun B after A fails or claim records persisted when its container was removed early. Remove only owned disposable storage; destroy the entire one-job VM after the job/cancellation using an out-of-band owner-approved mechanism. A job `finally` block alone cannot guarantee cleanup after host loss. Record cleanup/destruction disposition and unresolved residue; never reuse a failed VM.

Pilot06/Pilot07 Testcontainers create their own disposable databases, but safe cancellation/container/process cleanup and meaningful human lab receipts still need the same review. Pilot07 lab folder must be a fresh child of its existing dedicated `%LOCALAPPDATA%/ARG-Digital/AroNexa-Pilot07-Disposable` root with the required test marker; Pilot09 has its own dedicated root. Do not copy another lab folder or receipt.

## Recovery and unresolved teardown observations

The source method `pilot07NonemptyDisposablePostgresSnapshotRestoresToFreshDatabase` explicitly exports/restores an **unencrypted** nonempty disposable dump. Neither a passing method nor a genuine recovery acknowledgement proves encrypted recovery. `encrypted_recovery=NOT_IMPLEMENTED_IN_EXISTING_TEST` remains visible. No clinical/recovery implementation, cryptographic wrapper or recovery acceptance contract changed here. Encrypted recovery remains a separately scoped design/implementation/review requirement; no waiver or PASS is proposed.

The current product coordinator unconditionally exits2 and writes `full_verification=NOT_PASS`, even if its method matrix eventually becomes PASS. Do not suppress that exit or infer complete verification from its method counts. This is an explicit unresolved execution-contract blocker. A separately approved correction/disposition is needed before a full Central PASS can become possible.

Local ordinary verification logged Surefire's 30-second fork-shutdown timeout message and Hikari closed-connection shutdown warnings despite Maven BUILD SUCCESS/exit0 and343 passing cases. Mockito also logged its dynamic-agent warning. These are unresolved runtime/teardown observations; they do not establish a clinical defect or close earlier PG connection-refusal root causes. Preserve raw diagnostics privately, record a sanitized warning classification and investigate owned process/thread/container lifecycle separately. Do not increase timeouts, disable checks, skip tests or reinterpret the messages away under this review-only task.

## Normalized evidence mapping proposal (not implemented)

Existing collector/reporter accept strict schema1 with a single `full_maven` object and all eight gates PASS. Product `matrix-results.json` is a different schema and must be rejected as a direct reporter input. Prepare a reviewed schema/adapter change (proposed schema2 in the manifest), preserving every current required identity, gate, privilege boundary and receipt constraint:

| Retained gate | Proposed evidence / refusal condition |
|---|---|
| `exact_source_sha_and_clean_checkout` | Live current065cfea head/base/draft, clean source, exact QA SHA, request/run/attempt, source bundle and QA archive digests; source drift refuses. |
| `portable_java21_actual_forked_jvm_identity` | Observed Java21 home/version/runtime digest for both RC03 forks; no acceptance based on environment names or PowerShell PIDs. |
| `frontend_model_regression_and_connected_build` | Current-head actual frontend test/build output (existing minimum249); preliminary ce7fbbc ordinary evidence supplies neither. |
| `real_http_pg17_tenant_branch_staff_session_rls_negatives` | Actual search>=7, roles>=4, RLS>=8 with current PG17 identity and scoped negative assertions; verify matching method projections in ordinary results. |
| `chromium_login_search_registration_booking_checkin_daily_queue` | Actual RC03 A, exactly1 clean method result plus browser assertions; keep synthetic privacy restrictions. |
| `same_marked_database_distinct_backend_process_restart` | Actual RC03 B, exactly1 clean result, distinct JVM PIDs, same fresh DB marker and patient/appointment/check-in/queue identities. |
| `operator_workflow_on_connected_frontend` | Nonempty independent human workflow/observations in fresh Pilot09 lab plus exact artifact-bound receipt; Pilot07 human method remains mandatory in the matrix too. |
| `full_maven_failures_preserved` | Complete352-method inventory/result reconciliation across all lanes, no missing/duplicate/unknown/fail/error/skip/NOT_RUN, actual per-lane exits and aggregate exit/full_verification. The current exit2/NOT_PASS blocks this gate. |

The schema proposal adds inventory digest/count, sanitized per-lane counts/exits, method-result digest, missing/duplicate/unexpected/NOT_RUN lists, matrix/full-verification statuses, recovery scope and teardown observations. Preserve old full-Maven failure counts and all mandatory tests; do not flatten NOT_RUN into skips=0 or exit0. Any missing identity/report/teardown disposition is incomplete evidence. The expected complete JUnit total is352 unique methods, not343 ordinary cases. No schema1 PASS may be synthesized from current local JSON.

Continue separate untrusted Windows execution and privileged hosted status reporting. Only normalized synthetic evidence may leave execution; never upload raw logs/XML, authorization environment values, fictional staff sheets or original data. Bind the actual uploaded ZIP/API artifact ID/name/digest to the exact QA/source/request/run/attempt; the Git-content reference hashes in this proposal are not uploaded-artifact identities. Revalidate current source and latest independent human reviews/receipts before any reporter action. There is no workflow, dispatch-permission, reporter or schema implementation change in this preparation.

## Required independent review and administrator decisions

All boxes are pending; this agent submits no approval or receipt.

- [ ] Owner names a qualified independent human reviewer and operator, neither matching product/QA PR author under current guards; any role combination explicitly decided. Reviewer covers Maven/JUnit/Surefire inventory, PG17/RLS/marker identity, Windows/Docker cancellation and process ownership, Actions credentials/artifact provenance and synthetic-data handling.
- [ ] Reviewer confirms actual read access to both private repos and pinned history, the26-path manifest, product source/coordinator/tests, threat model, preliminary evidence, this handoff and earlier infrastructure package. Reviewer can view Actions artifacts, submit their own formal exact-revision review and issue disposition. No product source/status/admin credential is required for human review. Access is not presumed from a login.
- [ ] Independently inspect all26 candidate product paths and the changed-again Pilot05 file; confirm the evidence-only ce7fbbc-to065cfea delta and raw Git-content hashes. Approve/reject each proposed scope addition explicitly; plan fields are not that decision.
- [ ] Review lane ordering, discovery coverage, exactly-once totals, cross-lane acknowledgement isolation, externally supplied authorization authenticity, portable-JVM evidence and failure/skip/NOT_RUN retention. Request separately authorized provisioning/teardown and collector/reporter adaptations rather than treating documentation as an implementation.
- [ ] Resolve the unconditional coordinator NOT_PASS/encrypted-recovery boundary through a separately reviewed contract/correction. Preserve the unencrypted-only classification; do not waive encrypted recovery by relabeling the test.
- [ ] Separately authorize a teardown diagnostic if needed; preserve current timeout/security controls and actual failure evidence.
- [ ] Administrator explicitly decides the ephemeral interactive Windows/Linux-Docker policy exception, one-job runner topology/scope, isolated console and out-of-band destruction on cancellation/host loss. No enrollment occurs here.
- [ ] Administrator separately authorizes/protects `win11p-control-approval`, `win11p-disposable-execution`, `win11p-independent-report`, trusted-main restrictions and prevent-self-review; verifies any administrator bypass policy. Existing unrelated environments are not substitutes.
- [ ] After independent review, separately set exact future `WIN11P_AUTHORIZED_QA_SHA`, `WIN11P_REVIEWED_QA_SHA`, reviewer/operator identities and runner approval. A new QA diff invalidates old authorization pins until re-reviewed. No variable is set here.
- [ ] Verify least-privilege source-read and isolated status-write credential capabilities/expiry without revealing values; execution gets neither. Credential creation/change and trusted-main publication remain separate explicit administrator/owner decisions. Do not merge PR37 under this task.
- [ ] Before later independent acceptance, re-read live PR148 head, execute every required check on exact current source in a fresh lab, verify immutable artifact identities, actual phase JVM/DB proof and independent artifact-bound operator/reviewer dispositions. Only a matching Central PASS permits already-authorized gated integration.

## Next independently executable checkpoint

**Now:** independently review this exact QA draft revision and product065cfea. An independent reviewer can reproduce offline plan validation, scope-denial assertions and existing39 infrastructure tests without a Windows runner, operator consent, product execution or status credential. This is preparation evidence only.

**After separate execution authorization and an approved fresh isolated environment:** the first product diagnostic checkpoint is current-head discovery + ordinary verify via `powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/pilot/Invoke-Win11p-MavenMatrix.ps1 -ExpectedCommit 065cfea959bfe6fd1ad334a7ccae98f84a1ddf9a -Mode Ordinary`, plus the focused coordinator checks. Expected352 discovered methods,343 ordinary PASS,1 discovery PASS,8 guarded NOT_RUN, coordinator exit2/NOT_PASS. Record real observed counts even if they differ; do not turn the expected incomplete result into Central acceptance PASS. No such execution is authorized or run by this task; current Central scope/executor must still refuse.

**Full independent Reception checkpoint remains blocked** until scope promotion is independently reviewed and separately authorized, guarded provisioning/teardown and normalized mapping are implemented/reviewed, the coordinator contract blocker is resolved, protected topology/credentials/pins are explicitly authorized, and genuine operator inputs are available. Keep all eight gates and rule27 HOLD. WIN-11B remains NOT_READY.

## Preparation verification record

Actual offline preparation checks (also rerun after committing this review revision; exact QA commit is linked in PR37/issue38):

- `python -B scripts/check_qa_plans.py`: **2 plans structurally valid**, including WIN11P's unchanged eight gates; not activation.
- `python -B -m unittest discover -s scripts/tests -v`: **39 tests PASS, 0 failures/errors/skips**. Existing mocked/fixture infrastructure tests only; no product acceptance or status publication.
- Static reconciliation audit: **12/12 assertions PASS**: original eight gates; unchanged13-path allowlist; exact26 candidate paths; actual scope rejection; review pending/no execution authorization; both source/frontend pins; all reference digests/blobs; unique352/ordinary343 inventory;10 lanes/eight guarded/352 total; exact method/tag identities; five documentation-only source-delta paths; unchanged workflows/scripts/INT plan.
- `git diff --check`: **PASS** before staging; tracked changes are the four review-only paths listed above. Existing untracked Python caches remain untouched.
- Live GitHub lookup: product065cfea commit statuses **empty**; QA PR37 reviews **empty**. There is no independent exact-SHA PASS, request/run identity or reviewer disposition to use for rule27.

No Maven, npm, browser, Docker/database, workflow dispatch or port operation is part of these checks. No current infrastructure CI run is claimed here. The earlier39-test CI checkpoint remains separate historical evidence.

An independent reviewer can repeat the key scope-denial check from the QA checkout without product execution:

```powershell
python -B scripts/check_qa_plans.py
python -B -m unittest discover -s scripts/tests -v
@'
import json, sys
from pathlib import Path
sys.path.insert(0, 'scripts')
from win11p_contract import validate_scope
p = json.loads(Path('qa/plans/WIN11P_RECEPTION_E2E.json').read_text())
m = json.loads(Path('qa/reviews/QA38_MAVEN_LIFECYCLE_REVIEW.json').read_text())
assert len(p['authorized_changed_paths']) == 13
assert len(m['proposed_changed_paths']) == 26
assert m['execution_authorized'] is False
try:
    validate_scope(p, m['proposed_changed_paths'])
except ValueError:
    print('PASS: proposed expanded scope remains denied')
else:
    raise AssertionError('expanded scope was silently authorized')
'@ | python -B -
```

For full reference reconciliation, compare `git diff --name-only 1abb41ba76acef072001336d8b86d4a0d29ac6a2 065cfea959bfe6fd1ad334a7ccae98f84a1ddf9a` in a read-only product checkout with the26 manifest entries; check each `head_blob` using `git rev-parse 065cfea959bfe6fd1ad334a7ccae98f84a1ddf9a:<path>` and hash the bytes from `git show`. This inspection does not execute product source.
