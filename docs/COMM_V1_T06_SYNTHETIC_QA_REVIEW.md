# COMM_V1_T06 — Independent browser QA source and reviewer handoff
**Issue:** QA Central #19; source Development #82 and draft PR #83.
**Status:** QA SOURCE PREPARATION ONLY / UNMERGED / NOT RUN in QA Central.
**Product source SHA (at drafting):** fa7c11d689f18bcbd9b81296d52d39806738f8a0.
**Source repository:** ARG-Digital-Solutions/aronexa-healthcare-platform; same-repo PR targeting main.

## New browser acceptance checks
The new tests/commercial/opd-journey.spec.mjs is an independent, fictional-only Playwright suite against isolated localhost preview:
- Full seven-action receptionist → doctor → billing sequence and unchanged patient/encounter identifiers.
- Wrong-role action denied without model progress; demo persona switch clearly called out.
- Reset/reload leaves no persistent fictional visit data.
- 390px mobile viewport no horizontal overflow, labeled and focusable persona picker.
- Explicit synthetic-only/no-auth/no-API/no-persistence disclaimers.

Model test source remains in product PR #83 and must be checked out at its exact SHA; do not copy model fixtures into QA Central. Reuse reviewed existing network.spec.mjs as a separate positive guard against external/non-preview requests.

## Production QA plan activation — independently reviewed change required
This QA-only PR **does not** update the plan validator, COMM-V1 manual dispatch workflow, or source token permissions. The current secure QA Central commercial workflow allows only COMM_V1_T01/T03/T04; do not run T06 under another ID.

Before running T06 in GitHub Actions:
1. Conduct independent review of source PR #83, eight changed paths, exact head SHA, risk/clinical boundaries.
2. Independently inspect this QA test-only PR and ensure it cannot access real patient information or external destinations.
3. In **separate security-reviewed PR**, extend qa/commercial-plans validator, approved source SHA and eight-path registry, workflow dispatch choice/case and source-read scope without elevating permissions or relaxing existing fail-closed source verification. Pinned product SHA must be revalidated before activation.
4. After separately authorized merge/activation, dispatch T06 manually with synthetic-only acknowledgement and immutable source SHA. Record model test totals, Vite standalone build, Playwright cases, JUnit/traces/artifact and independent reviewer result.
5. The automation result applies ONLY to synthetic demonstration. It does not permit real clinical records, security review #45 closure, original Windows migration #31, merging a product PR, customer pilot or release.

## Restrictions
- No auto-merge, product source edits, credentials in app test processes, production API, customer data or shared Windows DB.
- Any backend, live registration, prescription finalization, financial posting, Windows installer or online SaaS release requires separate authorized security and clinical acceptance.
- Source-only status is NOT PASSED QA. Human independent review and actual execution evidence are mandatory before marking anything accepted.

**Disposition:** Ready for review-only test-source PR; QA Central T06 execution NOT RUN. Do not close QA #19.
