# Optional source-repository automation (NOT installed)

The central QA repository runs on:
- QA branch pushes/PRs;
- weekdays by schedule;
- manual `workflow_dispatch` with an app SHA or branch;
- optional `repository_dispatch` from the AroNexa product repository.

To activate immediate tests on each AroNexa PR, an authorized repository maintainer may review and install `aronexa-trigger-qa.yml` below in the **product** repository at `.github/workflows/`. This changes another repository and requires separate owner authorization. It does not merge code, start backend services, migrate data, or touch any original Windows DB.

Required private GitHub settings:
- In QA repository: `ARONEXA_SOURCE_READ_TOKEN` secret, fine-grained token with **Contents: read** on private AroNexa app repository; no write scopes.
- In source repository (only if automated dispatch is authorized): `ARONEXA_QA_DISPATCH_TOKEN` secret, token with **Contents: write** on QA repository to dispatch workflows. Use dedicated GitHub App installation token where possible.
- In QA repository: optional `ARONEXA_APP_REF` variable to select which safe synthetic revision the scheduled run checks. The initial fallback is pinned PR #61 head, not mutable `main`.
- When the product repo no longer serves the same synthetic demo, update the verified tests, guards and pin through a reviewed PR. Do not silently run the old expectations against a clinical production environment.
