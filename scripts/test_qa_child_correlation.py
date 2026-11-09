#!/usr/bin/env python3
"""Offline fail-closed regression for the *actual jq selectors* in the QA dispatcher.

No network, credentials, GitHub API, application checkout, or database.
Do not replace these with a hand-written approximation of production expressions.
"""
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = (ROOT / ".github/workflows/qa-cross-repo-handoff.yml").read_text(encoding="utf-8")
APP_SHA = "f8b7f7b8294be52df0336d5e619f43b55450c976"
REQUEST = "42595190272-2"
BOUNDARY = "2026-11-09T12:00:00Z"
FRESH = "2026-11-09T12:00:01Z"
STALE = "2026-11-09T11:59:59Z"

# Fail if the workflow removes or changes its matching expression without updating this test.
candidate_lines = [line for line in WORKFLOW.splitlines()
                   if "[.[] | select(.headBranch ==" in line]
assert len(candidate_lines) == 1, "Expected one exact child-run selector in production workflow"
line = candidate_lines[0]
assert line.count("'") == 2, "Expected the production jq selector on exactly one quoted line"
RUN_FILTER = line.split("'")[1]
job_match = re.search(
    r'if test "\$WATCH_EXIT" -eq 0 && jq -e --arg workflow "\$PLAN_WORKFLOW" \'(.*?)\' <<< "\$RESULT_JSON"',
    WORKFLOW, re.S
)
assert job_match, "Expected production job-evidence match expression"
JOB_FILTER = job_match.group(1)

def jq(expr, payload, vars=None, exit_on_false=False):
    # Production child search uses -r (empty means no match); job gate uses -e.
    cmd = ["jq", "-er" if exit_on_false else "-r"]
    for key, value in (vars or {}).items():
        cmd.extend(["--arg", key, str(value)])
    cmd.append(expr)
    return subprocess.run(cmd, input=json.dumps(payload), capture_output=True, text=True)

def child(id, title, when=FRESH, branch="main"):
    return {"databaseId": id, "displayTitle": title, "createdAt": when, "headBranch": branch}

valid_title = f"INT-REG02A {REQUEST} / {APP_SHA}"
valid_child = child(100, valid_title)
vars = {"k": REQUEST, "sha": APP_SHA, "after": BOUNDARY}
cases = [
    ("valid exact child", [valid_child], "100"),
    ("exact child selected over stale and similarly named candidates", [
        child(90,valid_title,STALE),child(105,f"INT-REG02A {REQUEST}0 / {APP_SHA}"),
        child(106,f"INT-REG02A {REQUEST} / {'a'*40}"),
        child(107,valid_title,FRESH,"feature/other"),valid_child], "100"),
    ("old green child rejected", [child(99,valid_title,STALE)], ""),
    ("wrong request suffix rejected", [child(99,f"INT-REG02A {REQUEST}0 / {APP_SHA}")], ""),
    ("wrong SHA rejected", [child(99,f"INT-REG02A {REQUEST} / {'a'*40}")], ""),
    ("non-main child rejected", [child(99,valid_title,FRESH,"feature/other")], ""),
    ("unrelated title prefix-only match rejected", [child(99,f"prefix {REQUEST} / {APP_SHA} trailing")], ""),
    ("empty result rejected", [], ""),
]
for label, runs, expected in cases:
    result = jq(RUN_FILTER, runs, vars)
    assert result.returncode == 0, (label, result.stderr)
    assert result.stdout.strip() == expected, (label, result.stdout, expected)
    print(f"PASS: {label}")

def job(name, conclusion="success"):
    return {"name": name, "conclusion": conclusion}

old_guard = job("Check approved source pins and disposable-only gate")
old_backend = job("Backend full regression + disposable PostgreSQL")
old_frontend = job("Independent frozen Reception/Appointment baseline")
new_guard = job("Check reviewed plan and exact synthetic PR source")
new_frontend = job("Pinned frontend build, contract, model and Playwright QA")

def complete(jobs, status="completed", conclusion="success"):
    return {"status":status,"conclusion":conclusion,"jobs":jobs}

acceptance = [
    ("original INTREG01 valid", "qa-int-reg01.yml",
     complete([old_guard,old_backend,old_frontend]), True),
    ("new INTREG02A valid", "qa-int-reg02a.yml",
     complete([new_guard,new_frontend]), True),
    ("REG02A missing frontend test job", "qa-int-reg02a.yml",
     complete([new_guard]), False),
    ("REG02A skipped guard", "qa-int-reg02a.yml",
     complete([job(new_guard["name"],"skipped"),new_frontend]), False),
    ("REG02A failed browser/frontend job", "qa-int-reg02a.yml",
     complete([new_guard,job(new_frontend["name"],"failure")]), False),
    ("REG02A cancelled", "qa-int-reg02a.yml",
     complete([new_guard,new_frontend],"completed","cancelled"), False),
    ("REG02A still running", "qa-int-reg02a.yml",
     complete([new_guard,new_frontend],"in_progress","success"), False),
    ("old INTREG01 missing backend", "qa-int-reg01.yml",
     complete([old_guard,old_frontend]), False),
    ("old INTREG01 skipped backend", "qa-int-reg01.yml",
     complete([old_guard,job(old_backend["name"],"skipped"),old_frontend]), False),
    ("old workflow used with new jobs", "qa-int-reg01.yml",
     complete([new_guard,new_frontend]), False),
    ("arbitrary workflow rejected", "qa-arbitrary.yml",
     complete([old_guard,old_backend,old_frontend]), False),
]
for label, workflow, payload, expected in acceptance:
    result = jq(JOB_FILTER,payload,{"workflow":workflow}, exit_on_false=True)
    ok = result.returncode == 0 and result.stdout.strip() == "true"
    assert ok == expected, (label, result.returncode, result.stdout, result.stderr)
    print(f"PASS: {label}")
print(f"PASS: {len(cases)} child-correlation and {len(acceptance)} workflow-result cases")
