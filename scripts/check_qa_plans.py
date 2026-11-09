#!/usr/bin/env python3
"""Static, offline validation of controlled QA Central plan documents."""
import json
import pathlib
import re
import sys

root = pathlib.Path(__file__).resolve().parents[1]
directory = root / "qa" / "plans"
# Deliberate allowlist: new plans and required checks require reviewed source changes.
reviewed_plan_specs = {
    "P01_T07_INT_REG_01": {
        "workflow": "qa-int-reg01.yml",
        "checks": {"source_scope_and_disposable_guard", "maven_verify_and_testcontainers", "frozen_frontend_build", "frontend_model_regression", "verified_playwright"},
        "paths": {
            "backend/src/test/java/com/argdigital/aronexa/patient/SyntheticRegistrationFrontendContractTests.java",
            "backend/src/test/resources/contracts/p01-t07-int-reg01-registration-v1.json",
            "docs/phases/P01_T07_INT_REG01_CONTRACT_AND_GAPS.md",
            "docs/phases/P01_T07_INT_REG01_BUILD_LOG.md",
        },
    },
    "P01_T07_INT_REG_02A": {
        "workflow": "qa-int-reg02a.yml",
        "checks": {"source_scope_and_disposable_guard", "frontend_build", "frontend_model_regression", "contract_preview_tests", "verified_playwright"},
        "paths": {
            "frontend/src/registrationContractPreview.ts",
            "frontend/test/registration-contract-preview.test.mjs",
            "docs/phases/P01_T07_INT_REG02A_SYNTHETIC_SEAM.md",
        },
    },
}

def fail(message):
    print(f"QA PLAN INVALID: {message}", file=sys.stderr)
    raise SystemExit(1)

plans = sorted(directory.glob("*.json"))
if not plans:
    fail("No reviewed QA plans found")
for path in plans:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError) as error:
        fail(f"{path.name}: {error}")
    plan_id = data.get("plan_id", "")
    if not isinstance(plan_id, str) or not re.fullmatch(r"[A-Z][A-Z0-9_]{5,60}", plan_id):
        fail(f"{path.name}: invalid plan ID")
    if path.stem != plan_id:
        fail(f"{path.name}: plan ID must match filename")
    if data.get("source_repository") != "ARG-Digital-Solutions/aronexa-healthcare-platform":
        fail(f"{plan_id}: wrong source repository")
    spec = reviewed_plan_specs.get(plan_id)
    if spec is None:
        fail(f"{plan_id}: plan has no independently reviewed allowlist")
    if data.get("qa_workflow") != spec["workflow"]:
        fail(f"{plan_id}: unapproved workflow for this plan")
    for name in ("source_baseline_sha", "frozen_frontend_sha"):
        if not isinstance(data.get(name), str) or not re.fullmatch("[0-9a-f]{40}", data[name]):
            fail(f"{plan_id}: {name} must be a 40-character SHA")
    for name in ("source_base_branch", "task_id"):
        if not isinstance(data.get(name), str) or not data[name].strip():
            fail(f"{plan_id}: missing {name}")
    paths = data.get("authorized_changed_paths")
    if not isinstance(paths, list) or not paths or len(paths) != len(set(paths)):
        fail(f"{plan_id}: authorized paths missing/duplicated")
    if not all(isinstance(p, str) and p and not p.startswith("/") and
               not any(c in p for c in "*?[]") and ".." not in pathlib.PurePosixPath(p).parts
               for p in paths):
        fail(f"{plan_id}: paths must be exact relative paths, no wildcards")
    if set(paths) != spec["paths"]:
        fail(f"{plan_id}: authorized changed paths differ from approved plan")
    checks = data.get("required_checks")
    if not isinstance(checks, list) or len(checks) != len(set(checks)) or set(checks) != spec["checks"]:
        fail(f"{plan_id}: exact required acceptance checks do not match approved workflow")
    if plan_id == "P01_T07_INT_REG_02A":
        if data.get("source_pr_number") != 67:
            fail(f"{plan_id}: only product PR #67 is approved")
        if data.get("approved_source_sha") != "f8b7f7b8294be52df0336d5e619f43b55450c976":
            fail(f"{plan_id}: unexpected source SHA")
        if data.get("source_baseline_sha") != "52809efbc077cd6abb6860d870cc487cc8eddc42":
            fail(f"{plan_id}: unexpected frozen frontend baseline")
    if type(data.get("qa_issue_number")) is not int or data["qa_issue_number"] < 1:
        fail(f"{plan_id}: QA issue number missing")
    if data.get("test_only") is not True or data.get("independent_review_required") is not True:
        fail(f"{plan_id}: test-only and independent review gates must be true")
    if data.get("customer_release_allowed_on_ci_pass") is not False:
        fail(f"{plan_id}: QA CI can never auto-approve customer release")
    if not (root / ".github/workflows" / data["qa_workflow"]).is_file():
        fail(f"{plan_id}: required workflow absent")
    print(f"QA PLAN VALID: {plan_id}, {len(paths)} authorized paths, {len(checks)} gates")
print(f"QA plans validated: {len(plans)}")
