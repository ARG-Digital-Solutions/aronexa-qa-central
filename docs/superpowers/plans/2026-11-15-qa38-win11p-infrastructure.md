# QA38 WIN11P infrastructure implementation plan
Authorized: owner task issue38; preparation and isolated tests only. Classification NOT_READY.

Goal: a manual-only reviewed WIN11P path, leaving INT-REG01 controller/workflow and product PR148 unchanged.
Alternative rejected: generalizing automatic cross-repo dispatch broadens trust and draft semantics unnecessarily.
Chosen design: strict plan-specific static validation; separate workflow_dispatch control, isolated execution and reporter jobs.
No activation follows from structural plan validity. Admin must pin authorized QA SHA, approve an ephemeral Windows interactive VM with Linux Docker, configure protected environments, and independently review the QA revision.
The existing GitHub-hosted-only policy needs explicit admin/owner exception for this proposed one-job ephemeral Windows runner. No runner enrollment is performed here.

- [ ] Write negative/unit contracts before implementation; observe missing-module failure.
- [ ] Implement strict plan, context, source-scope, XML, evidence/artifact and independent receipt validators using Python stdlib.
- [ ] Retain all legacy plan protections and all eight original WIN11P gates. Unknown plan/workflow pair fails closed.
- [ ] Add Windows Java21/Node24/Playwright runner for fresh marked PG17: full Maven outcome, focused security, jlinked Java RC03 phases, interactive operator lab. Publish only allowlisted normalized evidence.
- [ ] Add manual workflow restricted to trusted main and explicit admin SHA authorization; no changes to automatic INT-REG01 dispatch. Bundle source without credentials; Windows execution has no source/status secrets.
- [ ] Reporter validates artifact ZIP digest/identity, live exact draft PR head and an independent issue38 receipt tied to run/request/evidence digest. It never executes downloaded code.
- [ ] Test valid and negative paths, PowerShell parser and actionlint. Synthetic tests only; no VM/Docker execution, enrollment or credentials changes.
- [ ] Record actual results, unknowns and review checklist; update existing draft PR37 and issue38. No merge, Central PASS or product integration.
