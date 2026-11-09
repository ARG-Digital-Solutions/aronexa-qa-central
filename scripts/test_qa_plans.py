#!/usr/bin/env python3
"""P01-T07: offline negative-path acceptance for the reviewed QA plan registry.

Exercises the REAL plan validator in disposable directories, without GitHub
credentials, a database, a network connection, or any workflow dispatch.
"""
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

SOURCE = pathlib.Path(__file__).resolve().parents[1]
PLANS = ("P01_T07_INT_REG_01", "P01_T07_INT_REG_02A")
WORKFLOWS = ("qa-int-reg01.yml", "qa-int-reg02a.yml")

def isolated_fixture(root):
    (root / "scripts").mkdir()
    (root / "qa/plans").mkdir(parents=True)
    (root / ".github/workflows").mkdir(parents=True)
    shutil.copy2(SOURCE / "scripts/check_qa_plans.py", root / "scripts/check_qa_plans.py")
    for name in PLANS:
        shutil.copy2(SOURCE / "qa/plans" / (name + ".json"), root / "qa/plans" / (name + ".json"))
    for name in WORKFLOWS:
        shutil.copy2(SOURCE / ".github/workflows" / name, root / ".github/workflows" / name)

def run_validator(root):
    return subprocess.run([sys.executable, str(root / "scripts/check_qa_plans.py")],
                          capture_output=True, text=True, check=False)

def edit_plan(root, name, change):
    path = root / "qa/plans" / (name + ".json")
    body = json.loads(path.read_text(encoding="utf-8"))
    change(body)
    path.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")

def test_case(label, mutate, expect_fragment):
    with tempfile.TemporaryDirectory(prefix="aronexa-qa-plan-failclosed-") as folder:
        root = pathlib.Path(folder)
        isolated_fixture(root)
        mutate(root)
        result = run_validator(root)
        if result.returncode == 0 or expect_fragment not in (result.stderr + result.stdout):
            raise AssertionError(f"{label}: fail-closed rejection missing. "
                                 f"exit={result.returncode}, stdout={result.stdout!r}, stderr={result.stderr!r}")
        print(f"PASS: {label} correctly rejected")

def set_value(plan, key, value):
    plan[key] = value

with tempfile.TemporaryDirectory(prefix="aronexa-qa-plan-valid-") as folder:
    root = pathlib.Path(folder)
    isolated_fixture(root)
    result = run_validator(root)
    if result.returncode or "QA plans validated: 2" not in result.stdout:
        raise AssertionError(f"Known-good plans not accepted: {result.returncode}: {result.stderr}")
    print("PASS: both valid and distinct reviewed plans accepted")

test_case("unreviewed plan ID", lambda r: edit_plan(r, PLANS[1], lambda p: set_value(p, "plan_id", "UNREVIEWED_PLAN")), "QA PLAN INVALID")
test_case("unapproved workflow", lambda r: edit_plan(r, PLANS[1], lambda p: set_value(p, "qa_workflow", "qa-arbitrary.yml")), "unapproved workflow")
test_case("extra changed path", lambda r: edit_plan(r, PLANS[1], lambda p: p["authorized_changed_paths"].append("backend/src/main/java/Unsafe.java")), "authorized changed paths")
test_case("missing required contract tests", lambda r: edit_plan(r, PLANS[1], lambda p: p["required_checks"].remove("contract_preview_tests")), "required acceptance checks")
test_case("source SHA mismatch", lambda r: edit_plan(r, PLANS[1], lambda p: set_value(p, "approved_source_sha", "0"*40)), "unexpected source SHA")
test_case("baseline SHA mismatch", lambda r: edit_plan(r, PLANS[1], lambda p: set_value(p, "source_baseline_sha", "0"*40)), "unexpected frozen frontend baseline")
test_case("wrong product PR number", lambda r: edit_plan(r, PLANS[1], lambda p: set_value(p, "source_pr_number", 64)), "only product PR #67")
test_case("release authorized", lambda r: edit_plan(r, PLANS[1], lambda p: set_value(p, "customer_release_allowed_on_ci_pass", True)), "customer release")
test_case("review gate disabled", lambda r: edit_plan(r, PLANS[1], lambda p: set_value(p, "independent_review_required", False)), "independent review")
test_case("source repo differs", lambda r: edit_plan(r, PLANS[1], lambda p: set_value(p, "source_repository", "OTHER/example")), "wrong source repository")
test_case("duplicate source paths", lambda r: edit_plan(r, PLANS[1], lambda p: p["authorized_changed_paths"].append(p["authorized_changed_paths"][0])), "missing/duplicated")
test_case("backend regression removed from existing plan", lambda r: edit_plan(r, PLANS[0], lambda p: p["required_checks"].remove("maven_verify_and_testcontainers")), "required acceptance checks")
test_case("existing plan path modified", lambda r: edit_plan(r, PLANS[0], lambda p: p["authorized_changed_paths"].pop()), "authorized changed paths")
test_case("missing approved workflow file", lambda r: (r / ".github/workflows/qa-int-reg02a.yml").unlink(), "required workflow absent")
print("PASS: QA plan validator accepts valid plans and rejects 14 unsafe mutations.")
