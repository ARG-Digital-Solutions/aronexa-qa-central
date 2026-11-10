#!/usr/bin/env python3
"""Offline, fail-closed schema and allowlist for COMM-V1 QA plans (separate from REG01/REG02A)."""
import copy
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "qa" / "commercial-plans"
KNOWN = {
    "COMM_V1_T01": (75, "72638f1aa78e6f43c1043526c910c3656e81ebce", "consultation",
                    "COMM_V1_T01_SYNTHETIC_CONSULTATION.md", "consultation-model.test.mjs",
                    "consultation-preview.html", "vite.consultation.config.ts", "consultation.spec.mjs",
                    ("ConsultationPreview.tsx", "consultation.css", "model.ts", "preview.tsx")),
    "COMM_V1_T03": (78, "8b935abfb23ef818e248c2104e8fff55be5d6b52", "smart-rx",
                    "COMM_V1_T03_SMART_RX_SYNTHETIC.md", "smart-rx-model.test.mjs",
                    "smart-rx-preview.html", "vite.smart-rx.config.ts", "smart-rx.spec.mjs",
                    ("SmartRxPreview.tsx", "model.ts", "preview.css", "preview.tsx")),
    "COMM_V1_T04": (79, "c95b50d261ef457e336abf22faab30b720202b28", "billing",
                    "COMM_V1_T04_BILLING_SYNTHETIC.md", "billing-model.test.mjs",
                    "billing-preview.html", "vite.billing.config.ts", "billing.spec.mjs",
                    ("BillingPreview.tsx", "model.ts", "preview.css", "preview.tsx")),
}
CHECKS = sorted(("exact_sha_and_scope", "source_model_tests",
                 "standalone_preview_build", "independent_browser_acceptance"))

def validate(d):
    if not isinstance(d, dict):
        raise ValueError("plan must be object")
    plan_id = d.get("plan_id")
    if plan_id not in KNOWN:
        raise ValueError("unregistered plan id")
    pr, sha, module, doc, model, html, vite, suite, src = KNOWN[plan_id]
    expected_paths = sorted([
        "docs/phases/" + doc, "frontend/" + html,
        "frontend/" + vite, "frontend/test/" + model,
        *("frontend/src/" + module + "/" + p for p in src),
    ])
    constraints = {
        "source_repository": "ARG-Digital-Solutions/aronexa-healthcare-platform",
        "source_pr_number": pr, "source_base_branch": "main",
        "approved_source_sha": sha, "qa_issue_number": 16,
        "qa_workflow": "qa-commercial-previews.yml",
        "model_test": "test/" + model, "preview_page": html,
        "vite_config": vite, "browser_suite": suite,
        "synthetic_only": True, "independent_review_required": True,
        "customer_release_allowed_on_ci_pass": False
    }
    for key, expected in constraints.items():
        if type(d.get(key)) is not type(expected) or d.get(key) != expected:
            raise ValueError(f"{plan_id}: rejected {key}")
    if (not isinstance(d.get("authorized_changed_paths"), list) or
            sorted(d["authorized_changed_paths"]) != expected_paths or
            len(set(d["authorized_changed_paths"])) != 8):
        raise ValueError(f"{plan_id}: unexpected source path list")
    if sorted(d.get("required_checks", [])) != CHECKS:
        raise ValueError(f"{plan_id}: required checks were reduced")
    if not isinstance(d.get("feature"), str) or not d["feature"].strip():
        raise ValueError(f"{plan_id}: missing description")
    return True

def validate_source_pr(pr, plan):
    repo = plan["source_repository"]
    if (
        pr["number"] != plan["source_pr_number"] or
        pr["state"] != "open" or
        pr["head"]["sha"] != plan["approved_source_sha"] or
        pr["head"]["repo"]["full_name"] != repo or
        pr["base"]["repo"]["full_name"] != repo or
        pr["base"]["ref"] != plan["source_base_branch"] or
        pr["changed_files"] != len(plan["authorized_changed_paths"]) or
        not re.fullmatch(r"[0-9a-f]{40}", pr["base"]["sha"])
    ):
        raise ValueError("Source PR identity, head, base or file count differs from the reviewed plan")
    return pr["base"]["sha"]


def validate_changed_files(files, plan):
    if not isinstance(files, list) or any(
        not isinstance(entry, dict) or
        entry.get("status") != "added" or
        "previous_filename" in entry or
        not isinstance(entry.get("filename"), str)
        for entry in files
    ):
        raise ValueError("Source scope must contain only newly added files")
    if sorted(entry["filename"] for entry in files) != sorted(plan["authorized_changed_paths"]):
        raise ValueError("Source PR changed-path list differs from reviewed QA scope")


def main():
    paths = sorted(DIRECTORY.glob("*.json"))
    if {p.stem for p in paths} != set(KNOWN):
        raise ValueError("Missing/extra COMM-V1 plan; explicitly review any plan addition")
    for path in paths:
        plan = json.loads(path.read_text(encoding="utf-8"))
        if path.stem != plan.get("plan_id"):
            raise ValueError(f"{path}: filename mismatch")
        validate(plan)
        print(f"PLAN PASS {path.stem}: pinned PR #{plan['source_pr_number']} exact SHA, 8 paths, four checks")
    # Negative checks: accepting unknown plan, altered SHA/path or disabled release hold is a test failure.
    original = json.loads(paths[0].read_text(encoding="utf-8"))
    for label, change in (
        ("wrong SHA", {"approved_source_sha": "a" * 40}),
        ("unapproved PR", {"source_pr_number": 1}),
        ("release hold bypass", {"customer_release_allowed_on_ci_pass": True}),
        ("scope widening", {"authorized_changed_paths": original["authorized_changed_paths"] + ["backend/pom.xml"]}),
        ("missing check", {"required_checks": ["source_model_tests"]}),
        ("unknown workflow", {"qa_workflow": "arbitrary.yml"}),
    ):
        invalid = copy.deepcopy(original)
        invalid.update(change)
        try:
            validate(invalid)
        except ValueError:
            continue
        raise ValueError("Negative-path FAILED: " + label)
    print("COMM-V1 six plan negative-path cases PASS")

    additions = [{"filename": path, "status": "added"} for path in original["authorized_changed_paths"]]
    validate_changed_files(additions, original)
    for label, files in (
        ("rename", [{**additions[0], "status": "renamed", "previous_filename": "old.md"}, *additions[1:]]),
        ("deletion", [{**additions[0], "status": "removed"}, *additions[1:]]),
        ("modification", [{**additions[0], "status": "modified"}, *additions[1:]]),
        ("previous path", [{**additions[0], "previous_filename": "old.md"}, *additions[1:]]),
        ("duplicate path", [additions[1], *additions[1:]]),
        ("missing path", additions[1:]),
        ("extra path", [*additions, {"filename": "backend/pom.xml", "status": "added"}]),
    ):
        try:
            validate_changed_files(files, original)
        except ValueError:
            continue
        raise ValueError("Changed-file negative-path FAILED: " + label)
    print("COMM-V1 seven changed-file negative-path cases PASS")

    repo = original["source_repository"]
    source_pr = {
        "number": original["source_pr_number"],
        "state": "open",
        "head": {"sha": original["approved_source_sha"], "repo": {"full_name": repo}},
        "base": {"ref": "main", "sha": "a" * 40, "repo": {"full_name": repo}},
        "changed_files": 8,
    }
    validate_source_pr(source_pr, original)
    for label, change in (
        ("closed PR", {"state": "closed"}),
        ("wrong PR", {"number": 1}),
        ("stale SHA", {"head": {**source_pr["head"], "sha": "b" * 40}}),
        ("wrong source owner", {"head": {**source_pr["head"], "repo": {"full_name": "fork/repo"}}}),
        ("wrong base repository", {"base": {**source_pr["base"], "repo": {"full_name": "fork/repo"}}}),
        ("wrong base branch", {"base": {**source_pr["base"], "ref": "feature"}}),
        ("invalid base SHA", {"base": {**source_pr["base"], "sha": "main"}}),
        ("widened scope", {"changed_files": 9}),
    ):
        try:
            validate_source_pr({**source_pr, **change}, original)
        except ValueError:
            continue
        raise ValueError("Source PR negative-path FAILED: " + label)
    print("COMM-V1 eight mocked source PR refusals PASS")


def load_plan(plan_id):
    if plan_id not in KNOWN:
        raise ValueError("unregistered plan id")
    plan = json.loads((DIRECTORY / (plan_id + ".json")).read_text(encoding="utf-8"))
    if plan.get("plan_id") != plan_id:
        raise ValueError("plan filename mismatch")
    validate(plan)
    return plan

if __name__ == "__main__":
    try:
        if len(sys.argv) == 1:
            main()
        elif len(sys.argv) == 3 and sys.argv[1] == "--changed-files":
            plan = load_plan(sys.argv[2])
            validate_changed_files(json.load(sys.stdin), plan)
            print(f"Source file scope PASS {sys.argv[2]}: eight reviewed additions")
        elif len(sys.argv) == 3 and sys.argv[1] == "--source-pr":
            print(validate_source_pr(json.load(sys.stdin), load_plan(sys.argv[2])))
        else:
            raise ValueError("expected --changed-files PLAN_ID, --source-pr PLAN_ID or no arguments")
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print("COMM-V1 QA PLAN INVALID:", exc, file=sys.stderr)
        sys.exit(1)
