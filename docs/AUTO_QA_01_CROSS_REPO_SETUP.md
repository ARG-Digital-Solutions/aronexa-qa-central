# AroNexa AUTO-QA-01 — GitHub cross-repository handoff

**Status:** DRAFT / REVIEW ONLY. No secrets, labels, required checks or product merges are changed by this document.  
**QA repository:** `ARG-Digital-Solutions/aronexa-qa-central`  
**Development repository:** `ARG-Digital-Solutions/aronexa-healthcare-platform`

## Contract and data flow

1. A development PR includes exactly one QA plan label: `qa-plan:P01_T07_INT_REG_01` for the current milestone.
2. A trusted `pull_request_target` workflow in the product repository reads PR metadata, **never checks out or executes PR code**, and dispatches `aronexa-qa-request` to QA Central with PR number, exact SHA, plan ID and unique request key. It does not require the user to run PowerShell.
3. QA Central's `.github/workflows/qa-cross-repo-handoff.yml` checks out reviewed QA plans from its own `main`, validates the plan and exact GitHub product PR SHA / same repo / target base branch / active QA label, and selects a **known, allowed** QA workflow. No arbitrary user-provided shell commands or path executions.
4. The controller triggers `qa-int-reg01.yml` on QA Central `main` using its scoped `GITHUB_TOKEN`, passing exact SHA and unique request ID. Its backend test job checks out only the exact source SHA and runs **fresh synthetic PostgreSQL Testcontainers**, all Maven tests, and the frozen frontend/browser checks. The existing `qa-int-reg01.yml` retains its original manual mode.
5. After *all required child jobs* complete, a **separate, credential-isolated** reporter posts the commit status `aronexa/central-qa/P01_T07_INT_REG_01` to the exact application SHA. The status description includes the unique request ID. It also comments with an audit link on the configured QA Central issue (`#6` for INT-REG01).
6. The product PR workflow polls its **own** commit status and accepts only matching SHA + plan + unique request ID. On PASS it marks only the QA handoff check as successful; on failure/missing evidence it fails. **No merge, production database migration, deployment, UI-to-API activation, release approval, or independent security sign-off occurs automatically.**

## Credentials and settings (owner/operator actions)

Secrets must be configured from GitHub **Settings → Secrets and variables → Actions → New repository secret**. Prefer short-lived GitHub App installation tokens where available, otherwise scoped fine-grained tokens. Do not paste secrets into chat, workflow files or PR comments.

| Secret | Where | Minimum repository access | Use |
|---|---|---|---|
| `ARONEXA_QA_DISPATCH_TOKEN` | Development repository | QA Central repository only: **Contents: write** | POST `repository_dispatch` |
| `ARONEXA_SOURCE_READ_TOKEN` | QA Central repository | Product repository only: **Contents: read** (already observed working) | Verify product PR, checkout exact test SHA |
| `ARONEXA_DEV_STATUS_TOKEN` | QA Central repository | Product repository only: **Commit statuses: write** | Publish exact-SHA status; no source-code write permission |

Confirm **Actions** is enabled on both private repositories and the QA Central controller job may use `GITHUB_TOKEN` with `actions:write` to dispatch its **own** reviewed test workflow. The QA issue commenter requires `issues:write` on QA Central, granted only to the reporter job.

## Activation (not yet performed)

1. Independent reviewers inspect the QA Central and application workflow PRs, especially `pull_request_target` and token isolation. Verify source QA tests are not executed in the privileged dispatch or report job.
2. Approve and merge the QA Central automation PR. Then approve and merge the product **workflow-only** PR. Neither merge affects product PR #64.
3. Create and grant the two new secrets above (existing source read secret can be reused). **Do not authorize general Contents write on product code.**
4. After setup, label a relevant application PR with one reviewed plan label. Example (PR #64 remains **draft and cannot be merged automatically**):

```powershell
gh label create 'qa-plan:P01_T07_INT_REG_01' --repo ARG-Digital-Solutions/aronexa-healthcare-platform --color 0969da --description 'Use the reviewed QA Central INT-REG01 plan'
gh pr edit 64 --repo ARG-Digital-Solutions/aronexa-healthcare-platform --add-label 'qa-plan:P01_T07_INT_REG_01'
```

5. Watch the product `AroNexa - Central QA Handoff` run and QA Central `AroNexa Central QA - Cross Repository Handoff`, plus the child `AroNexa P01-T07 INT-REG01 Independent QA`. Verify the application commit status context and exact request key link to the same test child run. Confirm both complete. A green synthetic build is **not** independent sign-off.
6. Have an independent reviewer disposition the evidence and separately authorize the next development task.

The product handoff job **fails explicitly** when a PR lacks exactly one reviewed QA plan label or originates from an unauthorized fork. This prevents GitHub's skipped-job-as-success behavior. After activation, existing internal PRs without a reviewed plan may be blocked; do not invent a generic pass or suppress the gate. Register a suitable plan and apply its label before proceeding. Enforcement via GitHub protected branch/rulesets depends on the repository's subscription and org policies; current private repo ruleset API access was restricted when checked.

## Future QA tasks

- Add a new reviewed `qa/plans/<PLAN_ID>.json` with requirement IDs, exact allowed source scope, SHA/base, test classes/suites, reviewer and release gates, and a central QA issue ID.
- Add or update a corresponding independently reviewed **allowlisted QA workflow**, not an arbitrary `workflow` filename supplied by development. Update the explicit workflow allowlist in the QA controller and plan validator. The initial implementation supports **only `qa-int-reg01.yml`**. New plan IDs alone are not sufficient for unrelated features.
- Have development PR agents apply exactly one `qa-plan:<PLAN_ID>` label. Every code push re-evaluates the **current exact SHA**, never relying on stale run results.
- Keep QA outputs in QA Central's Actions logs/artifacts and issue records; source-coupled JUnit/Testcontainers tests remain versioned with the product source.
- The next coding agent may start *only an independently authorized task* after matching QA PASS and required manual approvals. GitHub Actions alone does not independently start a ChatGPT/Codex agent.

## Failure handling

- Unknown/malformed plan, external fork, out-of-scope source changes, missing secrets, invalid PR label, stale commit, skipped/failed child suite, missing report token or timeout: **fail closed**. Do not switch tests off or convert skip into PASS.
- If the QA controller fails before validating the PR, the source-side job will time out rather than claim PASS. The run logs show the blocker.
- Independent review/owner approvals remain mandatory. Neither workflow merges PRs, modifies shared DB, issues licences or deploys customer code.
- Existing PR #64 has a verified **test-only** CI PASS on `7f1fb76ce80a9fb838df06fc616e14f169bc2dd4` via https://github.com/ARG-Digital-Solutions/aronexa-qa-central/actions/runs/42585442420. The new automated handoff has **not** itself been executed.

## Reference documentation

- https://docs.github.com/en/rest/repos/repos#create-a-repository-dispatch-event
- https://docs.github.com/en/rest/commits/statuses#create-a-commit-status
- https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target
- https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow
