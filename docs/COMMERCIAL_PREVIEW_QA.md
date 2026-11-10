# Commercial-preview independent QA

This draft introduces a **manual GitHub-hosted** QA runner for Development PR #75, #78 and #79. Their exact approved SHAs and eight changed files are pinned in `qa/commercial/` plans, linked to QA issues #13, #14 and #15.

After review/merge into QA Central main, open Actions > AroNexa Commercial Preview Independent QA > Run workflow. Select PR, enter its current exact 40-character head SHA, acknowledge synthetic-only execution, and inspect validation, Node model tests, default TypeScript/Vite build, dedicated feature Vite build, Playwright browser tests, JUnit, HTML traces and audit SHA provenance.

A changed PR head SHA or file inventory is intentionally blocked pending review of updated QA plan. This workflow does not automatically dispatch from Development PRs and does not post commit statuses. Existing automatic handoff supports INT-REG01 only; add other allowlisted plans in a separate reviewed integration change.

Tests are synthetic only. No production URLs, original Windows database, real patient details, API, billing gateway, migrations, privileged test runtime or deployments. No merge or release is authorized by a passing CI run.
