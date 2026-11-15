# QA38 independent review and administrator authorization handoff
> Current review preparation: [Maven lifecycle proposal and handoff](QA38_MAVEN_LIFECYCLE_REVIEW_HANDOFF.md), with machine manifest `qa/reviews/QA38_MAVEN_LIFECYCLE_REVIEW.json`. Product head is now065cfea959bfe6fd1ad334a7ccae98f84a1ddf9a; preliminary local tests belong toce7fbbc0b7d6658e5c4f9a252dec98dfa5df5ef5. The earlier source/diagnostic snapshots below are historical. Current plan retains its13-path execution allowlist and must reject the proposed26-path source until separate review/authorization. Full independent execution remains blocked; this notice grants no approval.

Date: 2026-11-15. Status: NOT_READY / DRAFT_NOT_ACTIVATED.
No approval, merge, activation, runner enrollment, credential change or independent execution is performed by this handoff.

## Exact checkpoints and what they mean
- Infrastructure CI checkpoint: QA713e0526cfa0d9d5fff80d7d71f1a545a59cf43d, [run43713936302](https://github.com/ARG-Digital-Solutions/aronexa-qa-central/actions/runs/43713936302): successful plan validation, 39 offline tests and actionlint. This is preparation-code evidence, not WIN11P Windows acceptance.
- Product PR148 current HEAD verified via live API at **2026-11-15T12:36:14Z**: **89c985dfd9c1b8cb456e07bc1e6516785c038604**, draft, base codex/win11p-integrated-reception-e2e.
- Owner-acknowledged local Reception source: bce7a9d501f764b7ba9386225d96ba5f7b89c3aa. Its249 frontend +7 search-security +2 distinct-JVM tests and PIDs28052/6036 remain local evidence. The current head differs only by an evidence document; no independent SHA-equivalence waiver is granted.
- QA PR37 has no submitted reviews/requested reviewers. Both designated human identities remain unassigned. Reviewer account access cannot be verified before a real account is designated.
- Live inventory: **zero QA runners**; only the existing comm-v1-source-read environment exists, so all three proposed WIN11P environments are absent. **Zero repository Actions variables**, including all five WIN11P authorization/identity variables. Existing source-read/status secret names are present in QA and dispatch secret name in product; their values, scopes and expiry were not inspected.
- This documentation-only handoff creates a later QA PR head. It does not invalidate the713e052 CI checkpoint for unchanged execution inputs, but the reviewer must approve an exact current revision and the administrator must pin the exact future authorized main commit.

Today's head check is a snapshot. No independent execution is scheduled. The live product head MUST be checked again immediately before any future approved execution, and again before reporting; a later head change fails closed.

## 1. Independent reviewer selection
Owner must name a human GitHub User who did not author the product or QA implementation. Current control code rejects either PR author's login for both configured reviewer and operator roles, and rejects bot dispositions. AI implementation review is not independent approval.

Required review coverage (one qualified primary reviewer or a primary supported by named specialists):
- GitHub Actions security: trusted versus untrusted checkout, fine-grained credentials, protected environments, manual dispatch, review validity and stale-source races.
- Windows one-job VM isolation, interactive operator sessions, Docker Linux-container topology, Java21/jlink, Node24/Playwright, Maven/Surefire/Testcontainers and reliable VM destruction.
- PostgreSQL17 nonowner roles/RLS and tenant/branch/session/resource-negative evidence; ability to distinguish test adapters from production-source APIs.
- Artifact/provenance review: SHA256, ZIP/XML handling, actual testcase/count agreement, run/request/attempt correlation, distinct JVM PIDs and fresh database markers.
- Clinical-data minimization and safe handling of synthetic credentials, logs and staff sheets. This technical reviewer does not automatically provide clinical, regulatory, cryptographic or customer-release signoff.

The operator must be able to use the approved isolated VM console, follow fictional Reception steps, preserve marker/process ownership and record a truthful nonempty-session receipt. If the same independent human is proposed for operator and reviewer, owner must explicitly approve the role combination; never infer it from a matching login.

### Least-privilege human GitHub access
| Role | Minimum capability needed | Not needed for this task |
|---|---|---|
| Independent reviewer | Read private QA and product repos (including the pinned history/diff); view QA Actions logs/artifacts; submit a formal QA PR37 review on the exact revision; comment own disposition on QA issue38; assigned permission to review the relevant protected environment | Product Contents write, product status-write token, repository/org administration, merge/deploy rights |
| Independent operator | Read the task/source instructions and QA artifacts; comment own issue38 receipt; separately authorized access to disposable VM console | Product write/status credentials, original clinic DB access, repository administration |
| Review-requesting maintainer | Ability to request a review/assign the chosen person under repository policy | Approval on behalf of that reviewer |
| Administrator | Authorized management of the specific repo environments/variables/secrets and runner scope; org runner-group authority if an org group is chosen | Use of administrator identity as independent reviewer of own implementation |

GitHub permits read-access users to review/comment and describes who can request reviews: [PR review documentation](https://docs.github.com/en/pull-requests/reference/pull-request-reviews). Confirm actual private-repository, organization and required-review policies for the selected account. Do not grant source-write/admin access merely as a shortcut to review.
If the reviewer independently chooses API/CLI review submission, the credential needs selected QA repo Pull requests:write; reading reviews needs Pull requests:read: [review API permissions](https://docs.github.com/en/rest/pulls/reviews). Normal human web review need not create a new token. A successful API review permission check is not authorization for this agent to submit APPROVED.
No review invitation or permission grant is issued by this handoff.

## 2. Reviewer package manifest and access acknowledgement
All following files were verified present at QA713e052, and source evidence was inspected at product89c985d. Paths are relative to their repositories.

| Review material | Required files/evidence |
|---|---|
| Governing plan | QA qa/plans/WIN11P_RECEPTION_E2E.json; AGENTS.md; docs/AUTO_QA_01_CROSS_REPO_SETUP.md |
| Execution/permission design and receipt schema | QA docs/QA38_WIN11P_INFRASTRUCTURE_REVIEW.md |
| Proposed manual workflow | QA .github/workflows/qa-win11p-reception.yml; .github/actionlint.yaml; .github/workflows/qa-handoff-lint.yml |
| Validator and isolated controller | QA scripts/check_qa_plans.py; scripts/win11p_contract.py; scripts/win11p_control.py |
| Private execution and sanitization | QA scripts/Invoke-Win11pReception.ps1; scripts/Observe-Win11pPostgres.ps1; scripts/win11p_collect.py |
| Regression/negative evidence | QA scripts/tests/test_win11p_contract.py, test_win11p_collect.py, test_win11p_control.py, test_win11p_infrastructure.py; CIrun43713936302 |
| Implementation log and review limitations | QA docs/QA38_WIN11P_INFRASTRUCTURE_BUILD_LOG.md; docs/superpowers/plans/2026-11-15-qa38-win11p-infrastructure.md |
| Legacy protection comparison | QA .github/workflows/qa-cross-repo-handoff.yml, qa-int-reg01.yml and qa/plans/P01_T07_INT_REG_01.json; workflow/controller Git blobs remain unchanged |
| Product exact-source and local evidence | Product docs/windows/WIN11P_146_FICTIONAL_DATA_ACCEPTANCE_20261115.md at89c985d; historical docs/windows/WIN11P_RECEPTION_BUILD_LOG.md; issue146 |
| Product test lifecycle/failure diagnosis | Product backend/pom.xml; Pilot05DisposableDatabaseGuard.java; Pilot05SeparateJvmHttpTests.java; AppointmentCandidateHttpAcceptanceTests.java and the source runners named by the plan |
| Threat model and authorization decisions | Sections3-5 of this handoff and the runbook above |

Pinned browse roots: [QA713e052](https://github.com/ARG-Digital-Solutions/aronexa-qa-central/tree/713e0526cfa0d9d5fff80d7d71f1a545a59cf43d), [product89c985d](https://github.com/ARG-Digital-Solutions/aronexa-healthcare-platform/tree/89c985dfd9c1b8cb456e07bc1e6516785c038604).

Before review begins, the designated reviewer must acknowledge access to both private roots, current PR37 diff, source13-path diff/baseline, this handoff, all manifests, CI logs and sanitized local evidence/hashes. Presence/readability to this agent does NOT establish another person's access.
Raw local Surefire/Maven records may include generated development credentials. Do not copy them into issues/artifacts. Any further diagnostic access must use the controlled synthetic lab and sanitized observations, never original clinic data.

## 3. Bounded threat model for this QA infrastructure
Assets: product/QA source and private history; source-read/status credentials; test/receipt integrity; GitHub status identity; Windows host/engine isolation; synthetic account sheets and logs; original clinic data excluded entirely.
Trust boundaries: trusted hosted prepare -> hash-bound input artifacts -> untrusted ephemeral Windows execution -> normalized evidence -> trusted hosted reporter -> product commit status. Human review/console and administrator settings are separate boundaries.

| Threat/capability | Implemented or proposed control | Residual risk / reviewer decision |
|---|---|---|
| Arbitrary/forked/stale application source | Fixed repository/open draft PR148/head/base/branch and exact13 paths; clean source and SHA-bound Git bundle; recheck before report | Future head changes require fresh plan/review/execution. Source-authored tests can still be dishonest; independent source/evidence review is required |
| Unreviewed QA branch or unauthorized dispatch | Manual only; fixed QA repo, main ref, exact admin-authorized QA SHA, independent exact code review and protected environment approvals | Environments/variables currently absent. Administrator must not enable a draft/unreviewed revision |
| Execution stealing a privileged reporter credential | Execute job references neither product token; committed credential-free transport; separate hosted reporter never executes app/artifact code | Same-host processes/runner service still define trust. One-job VM, tight token scopes and guaranteed destruction are mandatory |
| Secret/PHI disclosure through files/logs/history | Private synthetic lab; allowlisted numeric/hash evidence; no raw properties/stack traces/staff sheets; short artifact retention | Git bundle contains reachable private source history, not just working files. Before execution, review historical sensitive-content risk and restrict QA artifact readers to authorized source readers. Absence of persisted HTTP credentials is not proof that historical source has no secrets |
| Reused host, container, port or real database | Default-deny enrollment; fresh-engine/no-existing-lab checks; localhost; exact pilot name/label/marker; read-only PG observer | Labels alone do not prove host isolation. Admin must approve topology, fresh VM, no clinic routes/mounts/backups and isolated engine; never enroll owner's working PC/session |
| Fabricated/stale/mixed artifacts | Trusted input hashes; exact API artifact ID/name/run/head/digest; ZIP digest/entries limits; request/attempt/source/QA identity | A compromised worker can fabricate its own reports. Artifact identity alone does not prove test truth; human operator/reviewer receipts and code review remain necessary |
| XML counters hiding failures or skips | Counter/case/outcome cross-checks; required minimums, no skipped/failed/empty required suites | Independently inspect actual execution and sanitized diagnostic categories; do not treat an infrastructure fixture test as product acceptance |
| Build JDK substituted for portable runtime | Both phase XML java.home AND Java21 checks; jlink file-inventory digest unchanged | Real Windows jlink/Surefire execution is still NOT_RUN for this QA revision |
| Same JVM or wrong database claimed as restart | Different positive PIDs; same RC03 marker; source PASS_B; actual PG17 observations | Does not prove Windows service restart, installed product durability or operator-record persistence beyond disposable lab |
| Empty/expired operator session or self-disposition | Nonempty patient/check-in counts; separate operator marker; configured human identities not authors; latest artifact-bound receipts | Counts do not prove clinical usability. Human must actually perform prescribed workflow; no clinical UAT/release inference |
| Configuration drift, stale review, revoked disposition | Exact execution-input diff against approved QA revision, latest review/receipts and live head/config checks | Admin bypass, account compromise, artifact access and changes after status publication require operational audit/recheck at handoff |
| Full-Maven red hidden by focused green | Full verify outcome/counts retained; any failure/error/skip/missing reports blocks positive status | Current guarded-suite orchestration mismatch below is unresolved; no blanket acknowledgements or exclusions to obtain green |

Scope excludes production clinical operation, offline licensing, signed installer, original-database migration/restore and clinical/legal release authorization. Those are still separate gates.

## 4. Remaining full-Maven issues: evidence-based classification
No full-Maven run was performed in this documentation task. The exact current head has no independent full-suite result. Historical counts below belong to their own environments/sources and must not be combined with focused green results.

| Recorded/current observation | Classification | What is established / what is not |
|---|---|---|
| Product issue146 owner checkpoint at55da40e:344 tests,3 PILOT06/PILOT07 acknowledgement failures plus1 Pilot05 context error | Historical guarded-test orchestration/safety refusals, with a context cause still requiring diagnosis | They are not demonstrated clinical-domain defects. Do not set acknowledgement variables globally |
| Product historical WIN11P_RECEPTION_BUILD_LOG:101 reported tests,0 assertion failures,41 errors; Docker unavailable | Documented environment limitation of that historical sandbox | Does not demonstrate Docker failure at current Windows head; initialization errors collapse class counts |
| Same historical report: Mockito inline maker could not attach | Documented JDK/sandbox tooling limitation in that run | Fresh full-JDK21 host capability still needs controlled verification; no patient/API defect established |
| Historical ephemeral PG connection refusals at51379/51719 | Root cause unresolved; could involve lifecycle, address/port routing, readiness or environment | Do not classify definitively as product or environment without fresh marked-lab diagnostics. Never probe/reuse historical ports or original5433/56017 |
| Current source default test discovery includes Pilot05SeparateJvmHttpTests; its Spring initializer requires disposable port/run marker/consent/phase. POM has no dedicated opt-in selection/exclusion profile. Current QA runner executes clean plain mvn verify before creating those phase settings | **Current source/QA test-orchestration gap established by code inspection**; expected safety refusal, not a confirmed clinical-runtime defect | Exact-head runtime failure is not newly executed here. Environment repair alone is insufficient to establish clean full verify. A separately approved execution matrix/source-test-lifecycle correction is needed; A/B/operator phases cannot be satisfied by blanket flags |
| Current guarded PILOT06/PILOT07 tests require explicit browser/recovery/operator consent and dedicated lab paths | Test lifecycle/consent requirements, not permission to suppress tests | Run only through approved synthetic runners; preserve every required gate and actual executed-case evidence |
| Earlier RC03 fixed port collision and digit-containing fictional prefix | Historical environment conflict plus corrected test-fixture defect | Bounded local Reception rerun passed atbce7a9d; this does not resolve full verify or establish production-source runtime readiness |
| Current-head functional/clinical defects beyond the focused tests | NOT DETERMINED | No new clinical defect is asserted; absence of current full-suite evidence is not evidence of correctness |

Required next diagnostic work, only under a separately authorized bounded task: define the complete required-suite execution matrix, preserve guard/refusal tests and dedicated A/B/operator execution, collect fresh sanitized failures with exact source/QA/tool versions and database markers, and distinguish reproducible lifecycle defects from host/network/tool failures. Do not modify POM selection, skip assertions, use package-only diagnostics, fake credentials or set indiscriminate acknowledgements in this handoff.
The current infrastructure must stay red/not-executed as appropriate until a genuine complete clean result exists.

## 5. Administrator authorization checklist (all pending; no action executed)
For each item record named decision owner, explicit approval/denial, timestamp, exact revision and evidence link. A reference in YAML or a successful static CI check is not an approval.

### People and review
- [ ] Owner designates qualified independent reviewer and operator; confirms authorship conflict checks and any role combination.
- [ ] Each account demonstrates access to the package above, Actions artifacts, its own issue38 receipt and applicable environment-review UI.
- [ ] Reviewer submits actual code review on exact PR37 revision. Review is not a merge, runtime disposition or customer-release approval.
- [ ] Owner separately authorizes any required publication to trusted main. This task expressly does not authorize merging PR37.

### Ephemeral Windows topology and policy
- [ ] Explicitly approve a bounded exception to the current GitHub-hosted-only QA policy, or reject the proposed topology. Do not silently amend AGENTS/policy.
- [ ] Dedicated Windows/X64 one-job ephemeral runner, label aronexa-win11p-ephemeral, with approved Linux-container Docker engine and interactive independent operator console.
- [ ] Preprovision Java21/JDK+jlink, Node24, Maven, Python, PowerShell and Playwright prerequisites. No borrowed persistent working PC, active session, existing container, service or user worktree.
- [ ] Isolated network/storage: no original/customer DB routes, credentials, mounts, dumps, backup media or shared Docker engine; browser/API/PG loopback only.
- [ ] Restrict runner group/repository/workflow use as supported; record registration authority, one-job configuration and VM/engine destruction on success/failure/cancel/timeout. Validate protections before enrollment.
- [ ] Review source-history confidentiality and artifact-reader access/retention. Private logs/staff sheets remain only in disposable VM; destroy them with the VM.

### Protected environments and credentials
- [ ] Create/configure only after separate authorization: win11p-control-approval, win11p-disposable-execution, win11p-independent-report. Do not repurpose existing comm-v1-source-read.
- [ ] Required independent reviewers, prevent-self-review, main-only deployment restrictions and reviewed administrator-bypass policy. Verify feature support in this private repository; absent rules fail operational authorization.
- [ ] ARONEXA_SOURCE_READ_TOKEN: selected product repo Contents:read + Pull requests:read only; source checkout/metadata in trusted prepare/report. Verify capability/expiry without exposing value.
- [ ] ARONEXA_DEV_STATUS_TOKEN: selected product repo Commit statuses:write only (plus metadata access); reporter final step only, preferably protected environment secret. No product Contents write/merge/deploy scope.
- [ ] New workflow GitHub token: prepare Contents:read/Pull requests:read; execute no product credentials; reporter QA Contents:read/Pull requests:read/Actions:read/Issues:write. Do not broaden the existing automatic dispatcher or INT-REG01 permissions.
- [ ] Existing product ARONEXA_QA_DISPATCH_TOKEN is not required by this manual path and must not be widened or exposed to execution.
- [ ] Do not create/change/rotate any credential under this handoff; capability failures require explicit separate admin authorization.

### Exact pins and execution authorization
- [ ] WIN11P_REVIEWED_QA_SHA equals the exact independently approved PR37 code revision.
- [ ] WIN11P_AUTHORIZED_QA_SHA equals the actual separately authorized trusted-main workflow commit that will execute, not a historical CI hash by convenience. Controller must find execution inputs unchanged from reviewed revision.
- [ ] Configure the same protected identities/values visible to control/report: WIN11P_REVIEWER_LOGIN, WIN11P_OPERATOR_LOGIN, WIN11P_WINDOWS_RUNNER_APPROVED=true only after real enrollment approval.
- [ ] Immediately before dispatch, read PR148 live head/draft/base and compare to plan source_expected_head_sha and frozen_frontend_sha; current snapshot89c985d is not an evergreen authorization. Any drift stops execution and requires fresh review.
- [ ] Resolve/authorize diagnosis of full-Maven orchestration gap above before expecting a complete clean run. No scope escalation or implicit test waiver.
- [ ] Manual dispatch only after all explicit decisions; code rechecks before execution/report. Do not convert PR148 to ready or apply an activation label as a shortcut.

## 6. Eight-gate preservation and final evidence receipt
All eight checks remain required and independently NOT_RUN at this handoff:
1. exact_source_sha_and_clean_checkout
2. portable_java21_actual_forked_jvm_identity
3. frontend_model_regression_and_connected_build
4. real_http_pg17_tenant_branch_staff_session_rls_negatives
5. chromium_login_search_registration_booking_checkin_daily_queue
6. same_marked_database_distinct_backend_process_restart
7. operator_workflow_on_connected_frontend
8. full_maven_failures_preserved

Before leaving rule27 HOLD, verify actual successful required jobs, exact product/QA SHA, run/request/attempt IDs, artifact API identity and ZIP digest, normalized counts with zero failures/errors/skips, unchanged portable runtime and actual JVM homes/versions, distinct PIDs/same RC03 marker, PG17 observations, separate nonempty operator marker, latest independent receipts and source-head freshness.
Record real disposition per gate in issue38. Missing or failed evidence stays BLOCKED/NOT_RUN; infrastructure CI cannot be substituted.

## 7. Handoff actions and checks actually performed
Read-only live metadata: PR heads/reviews, confirmed CI run, environment protections inventory, runner inventory, variable names, secret names and exact-source status list. No secret values read.
Static source inspection: POM/default discovery, guarded lifecycle requirements, runbook/manifest/code/tests and current exact plan pins.
Preservation checks: clean tracked QA tree before this new document; original INT-REG01 workflow/controller diff against baseline empty; all eight plan check strings retained; no workflow/runtime source edits.
No tests, Docker, VM, product acceptance or independent execution were rerun in this documentation task. Prior39-test CI is linked as prior verified infrastructure evidence, not recounted as new clinical acceptance.
No self-approval, review request, merge, activation, enrollment, credential change, original DB access or deployment occurred.

### Actual command/evidence log for this handoff
- gh pr view 37 / gh pr view 148 with head/draft/review fields: QA713e052 and product89c985d verified; no independent review or reviewer request.
- gh run view 43713936302: completed/success at QA713e052; historical infrastructure result only, not rerun here.
- gh api QA environments: total1 (comm-v1-source-read only); all proposed WIN environments absent. gh api QA actions/runners: total0. No settings mutated.
- First variable-name jq query failed due native-shell quoting. Retried through ConvertFrom-Json, names only: total0 variables, no WIN11P entries. No credential values printed.
- gh api QA/product actions/secrets, names only: existing source/status/dispatch names present; capabilities/expiry unknown.
- gh api product pulls/148 plus UTC clock: source89c985d confirmed at2026-11-15T12:36:14Z, draft/base match; exact-source status list empty.
- git ls-tree at QA713e052 and static source reads: package files verified; lifecycle/acknowledgement requirements and plain full-verify invocation inspected. A mistaken QA-script read against the product directory found no file; correct QA worktree inspection followed, with no mutations.
- git diff --exit-code against baseline for INT-REG01 workflow/controller: PASS (unchanged). git diff --exit-code QA713e052..handoff-head for scripts/.github/qa-plans/package manifests: PASS (no execution-input change). git diff --check: PASS.
- Only this handoff Markdown file changed. No new Maven/Windows/Docker/clinical test outcome is claimed. A live head check must still be repeated immediately before any future authorized independent execution.
