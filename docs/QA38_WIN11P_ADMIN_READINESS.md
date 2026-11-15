# QA38 runtime and administration evidence — 2026-11-15

Disposition: **DRAFT_NOT_ACTIVATED / activation blocked / NOT_RUN / NOT_READY / rule27 HOLD.** This is a configuration proposal and read-only capability record under standing owner authorization. It supplies no human review, operator activity, security exception approval, runner enrollment, credential grant, dispatch, source merge, database acceptance or release decision.

## Working Linux toolchain

All installations are under this task's scratch tree; no product/QA checkout or system package installation was changed. The cloud package helper `/usr/local/bin/cloud-agent-packages` is absent, so publisher archives were installed locally after reading the cloud runtime Packages and Networking references. Proxy/TLS settings were preserved.

| Tool | Verified version | Usable location |
|---|---|---|
| PowerShell | 7.7.0 / Debian13 Linux X64 | `/workspace/work/qa38-engineering/runtime/bin/pwsh` |
| Maven | 3.9.11 | `/workspace/work/qa38-engineering/runtime/bin/mvn` |
| Temurin JDK | 21.0.13+9 LTS, javac and jlink21.0.13 | `/workspace/work/qa38-engineering/runtime/tools/jdk-21.0.13+9` |
| Docker | Client/daemon29.9.2, rootless Linux | `/usr/local/bin/docker` |
| gh | 2.46.0 | `/usr/bin/gh` |

Other installed versions: git2.52.0, Python3.12.14, Node24.22.1, npm11.9.0, curl8.14.1 (`evidence/other-tool-versions.json`).

Publisher verification records are `evidence/powershell-install.json` (SHA256), `maven-install.json` (SHA512), and `jdk-install.json` (SHA256). Each records the exact archive/checksum provenance and matched digest. PowerShell's publisher checksum text is UTF16; its initial UTF8 decode failed before extraction, then explicit BOM decoding and digest verification succeeded. Initial raw PowerShell launch failed because its default `/home/agent/.cache/powershell` is read-only. The launcher sets only XDG cache/config/data paths inside scratch and passes all arguments unchanged. Its `PSVersionTable` smoke passed. No `$HOME` override is used.

The Maven launcher fixes `JAVA_HOME` to the verified full JDK and `-Dmaven.repo.local` to task scratch. It removes `GH_TOKEN`, `GITHUB_TOKEN`, `ARONEXA_SOURCE_READ_TOKEN`, `ARONEXA_DEV_STATUS_TOKEN`, `ARONEXA_QA_DISPATCH_TOKEN` and `SSH_AUTH_SOCK` from Maven and its children. The parent should also remove those credentials before launching any product coordinator. Use the pwsh launcher rather than the raw binary. Maven `-version`, javac `-version`, jlink `--version`, and pwsh version all returned0. The preinstalled `/usr/bin/java` was a Java21.0.13 JRE without javac; it is not the selected build JDK.

```sh
export PATH=/workspace/work/qa38-engineering/runtime/bin:$PATH
export JAVA_HOME=/workspace/work/qa38-engineering/runtime/tools/jdk-21.0.13+9
mvn -version
pwsh -NoLogo -NoProfile -Command '$PSVersionTable.PSVersion.ToString()'
```

No product test, Maven build, PostgreSQL container, PowerShell product runner or operator workflow was executed by the runtime/admin agent. Local runtime installation and version probes do not establish portable-Windows or acceptance evidence.

## Current machine and isolation limits

Read-only `cloud_environment.environment_status` returned current/running/connected cloud observations, enforced unrestricted egress, remote desktop capability enabled with state unknown, and no configured secrets, runtime variables or outbound identities. Shell capability names were only `GH_TOKEN` and `GH_PAGER`; no values were printed or copied. Provider-level empty secret inventory does not imply the process lacks a GitHub credential: gh authenticates from `GH_TOKEN`.

This is Linux6.18.57 / Debian13 / X86_64, uid1000 `agent`. It is not the separately reviewed interactive Windows/X64 one-job runner. A possible Linux desktop is not evidence of the retained Windows operator gates.

`docker info` proves a reachable rootless daemon, built-in seccomp and cgroup namespace; storage driver vfs, cgroupv2, cgroup driver `none`. The initial daemon inventory contained0 containers,0 images,0 volumes, and only Docker's bridge/host/none networks. No broad cleanup was performed. `unshare --user --map-root-user true` failed1 because `/proc/self/uid_map` is read-only; an extra nested user namespace was not established. Rootless Docker is useful for owned synthetic Linux tests but does not prove Windows host/engine one-job isolation, destruction guarantees, a private interactive console, credential absence or restricted network routes. Those remain unverified.

Read-only records: `evidence/runtime-capabilities.json` and `evidence/isolation-readonly.json`.

## Actual GitHub capability results

`gh auth status` succeeded for `argsolutions2017` using `GH_TOKEN`. Only a redacted token line was retained. API response header `github-authentication-token-expiration` was **2026-11-15 20:27:38 UTC**. `x-oauth-scopes` was empty; that header does not enumerate fine-grained/integration permissions. Repository metadata reported account `permissions.admin=true`, but actual integration endpoint authorization below failed. Account role and token capability are distinct.

| GET endpoint family | Actual result | Implication |
|---|---|---|
| `/user`; repository metadata | 200 | Current identity and metadata reads work |
| Both repo `/actions/runners` | 403, `Resource not accessible by integration`; accepted permission administration=read | Runner inventory is **unknown**, not empty |
| Both repo `/actions/variables` | 403; actions_variables=read | Variable names/pins **unknown** |
| Both repo `/actions/secrets` | 403; secrets=read | Secret names and dedicated credential existence **unknown** |
| Both repo `/actions/permissions`, `/actions/permissions/workflow` | 403; administration=read | Actions policy/default-token settings **unknown** |
| Both repo `/branches/main/protection` | 403; administration=read | Classic protection details **unknown** |
| Organization `/actions/permissions` | 403; organization_administration=read | Organization policy **unknown** |
| Organization `/actions/runner-groups` | 403; organization_self_hosted_runners=read | Restriction support/group state **unknown** |
| Both repo `/environments` | 200 | QA has only `comm-v1-source-read`; product has0. All three WIN11P environments are absent |
| QA `/rulesets`; main branch | 200 | No listed rulesets; branch main reports protected=false |
| Product `/rulesets/26323499`; main branch | 200 | Active Protect-main ruleset, main protected=true; no bypass actors, current_user_can_bypass=never |
| QA `/actions/workflows` | 200 | Six existing workflows; WIN11P workflow absent from trusted main |

The existing unrelated `comm-v1-source-read` environment has a branch-policy rule, `can_admins_bypass=true`, and no required-reviewers rule in its API response. It is not an approved substitute for WIN11P environments. Product Protect-main requires existing status checks and resolved review threads, but `required_approving_review_count=0`; that configuration is not proof of independent review.

**Confidentiality discrepancy:** both live repository metadata responses report `visibility=public`, `private=false`, `allow_forking=true`, whereas existing handoff prose assumes private roots. No visibility setting was changed by this task. Review the actual source/history/log/artifact reader model before activation; private-reader assumptions cannot be carried forward from old text. No full source-history audit was performed here.

Exact API endpoints, exit codes, accepted-permission/expiry headers, and sanitized returned metadata are retained in `evidence/github-admin-readonly.json` and `evidence/github-security-readonly.json`. The 403 responses are provider authorization failures, not an automatic approval-review rejection. No new admin credential was requested or created, and no connector credential was exported. Because gh was authenticated, no GitHub plugin fallback or token copying was necessary.

## Concrete pending configuration proposal

Machine-readable desired settings are in `admin-proposal.json`. All approval references, reviewed pins, human identities and isolation proofs are null/false. `WIN11P_WINDOWS_RUNNER_APPROVED` remains **false** in the proposal; no corresponding live value was assumed or written.

1. **Review a bounded policy exception first.** QA AGENTS rule4 currently requires ephemeral GitHub-hosted runners. The manual workflow proposes self-hosted Windows/X64. Record a narrowly scoped exception for this workflow/plan/exact approved revisions, with owner decision, qualified security review, lifecycle/isolation evidence and revocation/expiry terms. This file is the proposal, not the review. If supported GitHub-hosted interactive Windows execution can meet every retained gate, review that alternative explicitly; do not relabel this Linux environment.
2. **Verify isolation before enrollment.** Dedicated one-job ephemeral Windows VM; sole-job runner service identity; label `aronexa-win11p-ephemeral`; private interactive console for the designated operator; Java21/Node24/Python/Maven/PowerShell/Playwright; disposable Linux Docker/PG17 engine with no shared/original databases, no production secrets/VPN/routes and loopback-only database publishing. Restrict the runner group to QA Central and, where supported, `.github/workflows/qa-win11p-reception.yml@refs/heads/main`. Reject reused VM, existing containers/lab directories/ports, inherited product credentials and unverified engine endpoints. Record an out-of-band destruction controller and concrete VM **and engine** disposal evidence for success, failure, timeout, cancellation, interrupted teardown and runner/host loss; the controller must not depend on the vanished worker process; runner `--ephemeral` alone proves one job, not host/engine destruction. Review encrypted recovery separately; no unencrypted substitute satisfies that acceptance requirement.
3. **Protect three exact environments.** `win11p-control-approval`, `win11p-disposable-execution`, `win11p-independent-report`: required owner-designated independent reviewers; prevent self-review; main-only branch deployment rule (no tag wildcard); administrator bypass disabled or separately reviewed explicit policy. Verify actual feature support by reading configured protection_rules/deployment-branch-policy APIs. Unsupported/missing controls deny activation. Do not modify the unrelated COMM environment.
4. **Set pins only after reviewed code exists on trusted main.** `WIN11P_AUTHORIZED_QA_SHA` = exact separately authorized trusted-main workflow commit; `WIN11P_REVIEWED_QA_SHA` = actual independently approved QA revision with identical executable inputs; reviewer/operator logins = verified designated humans who satisfy implementation-author conflicts. Record any owner-authorized role combination. Current PR authors, this agent and AI review do not supply human approvals. Recheck current PR148 head, base, draft state, exact26 paths, source/frontend hashes, all eight retained requirements and plan status immediately before execution. An empty/past/stale pin denies execution.
5. **Verify selected-repository credentials without values.** Prefer short-lived installation credentials. `ARONEXA_SOURCE_READ_TOKEN`: product repository only, Contents:read + Pull requests:read + implicit Metadata:read; exposed only during hosted prepare/read-only report metadata steps, never execution. `ARONEXA_DEV_STATUS_TOKEN`: product repository only, Commit statuses:write + implicit Metadata:read; exposed only in the final isolated hosted reporter status step, never checkout/build/browser/source execution. Audit token issuance grants, expiry and installation/repository selection through the owner/admin provider UI or privileged metadata API; ordinary successful reads do not prove denied writes. Source checkout uses persist-credentials:false. Do not use this session's general gh credential as either workflow secret. Existing dedicated secret capabilities/expiry remain unknown because secret-name metadata is denied; no new credential is justified by this record alone.
6. **Retain job privilege boundaries.** Manual workflow only, no new product auto-dispatch activation. Prepare/report stay on GitHub-hosted Linux; execute receives only hash-bound committed input artifacts and no source-read/status-write credential. Review built-in runner/download/upload tokens and runtime storage exposure as part of VM threat model. Reporter may read exact GitHub artifact bytes and metadata, source metadata/reviews and issue receipts, but executes no source/artifact code. Its own limited `GITHUB_TOKEN` needs only existing declared permissions (QA issue write only in reporter); product status scope remains separate. `ARONEXA_QA_DISPATCH_TOKEN` is unrelated to this manual-only activation and is not created here.
7. **Evidence remains required after configuration.** All required methods/lanes and eight gates must actually execute, counts/exits/skips reconcile exactly, source/QA/request/run/attempt/artifact digests remain bound, and actual latest artifact-bound operator/reviewer receipts must exist. Missing Windows/operator/encrypted-recovery evidence stays NOT_RUN/NOT_PASS/NOT_READY. Configuration approval is not a Central PASS.

## Readiness verification performed

```sh
python3 /workspace/work/qa38-engineering/runtime/verify_admin_readiness.py
```

Actual exit **2**; `decision=ACTIVATION_BLOCKED`, `settings_applied=false`, `credentials_created=false`, `runner_enrolled=false`. The JSON result is `evidence/admin-readiness.json`. It verifies the captured configuration against the proposed requirements and preserves unknown API capabilities as blockers. It performs no network requests or mutations and intentionally never grants dispatch authority, even if a future proposal has all booleans set; a fresh live configuration and human review are still necessary.

No owner question is needed for the completed routine tool installs/read-only checks. Activation remains pending the concrete policy/isolation/credential evidence above, with actual 403 capability limitations preserved. Nothing was silently configured to bypass them.
