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
    print("COMM-V1 six security/scope negative-path cases PASS")

if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print("COMM-V1 QA PLAN INVALID:", exc, file=sys.stderr)
        sys.exit(1)
