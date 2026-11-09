#!/usr/bin/env python3
"""Static, offline validation of controlled QA Central plan documents."""
import json
import pathlib
import re
import sys

root = pathlib.Path(__file__).resolve().parents[1]
directory = root / "qa" / "plans"
required_checks = {"maven_verify_and_testcontainers", "verified_playwright"}
valid_workflows = {"qa-int-reg01.yml"}

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
    if data.get("qa_workflow") not in valid_workflows:
        fail(f"{plan_id}: unknown unapproved QA workflow")
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
    checks = data.get("required_checks")
    if not isinstance(checks, list) or not required_checks.issubset(set(checks)):
        fail(f"{plan_id}: missing required backend and browser checks")
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
