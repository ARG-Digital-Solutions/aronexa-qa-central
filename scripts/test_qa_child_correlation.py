#!/usr/bin/env python3
"""Offline fail-closed tests of the real jq selectors and identity gate in QA Central.

No network, credentials, app checkout, migrations, or workflow dispatch.
These fixtures do not replace independent live controller security review.
"""
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = (ROOT / ".github/workflows/qa-cross-repo-handoff.yml").read_text(encoding="utf-8")
APP_SHA = "f8b7f7b8294be52df0336d5e619f43b55450c976"
QA_SHA = "a" * 40
OTHER_SHA = "b" * 40
REQUEST = "42595190272-2"
BOUNDARY = "2026-11-09T12:00:00Z"
FRESH = "2026-11-09T12:00:01Z"
STALE = "2026-11-09T11:59:59Z"
TITLE = f"INT-REG02A {REQUEST} / {APP_SHA}"
WF_PATH = ".github/workflows/qa-int-reg02a.yml"
WF_ID = 1234

# The child-run filter is directly extracted from the privileged production workflow.
candidate_lines = [line for line in WORKFLOW.splitlines()
                   if "[.[] | select(.headBranch ==" in line]
assert len(candidate_lines) == 1, "Expected exactly one production child-run selector"
line = candidate_lines[0]
assert line.count("'") == 2, "Production child-run selector must fit one quoted line"
RUN_FILTER = line.split("'")[1]
assert "headSha == $qasha" in RUN_FILTER and "displayTitle == $title" in RUN_FILTER
assert "if length == 1" in RUN_FILTER, "Multiple matching child runs must fail closed"

job_match = re.search(
    r'if test "\$WATCH_EXIT" -eq 0 && jq -e --arg workflow "\$PLAN_WORKFLOW" --arg qasha "\$QA_SHA" \'(.*?)\' <<< "\$RESULT_JSON"',
    WORKFLOW, re.S
)
assert job_match, "Expected one source-derived job acceptance predicate"
JOB_FILTER = job_match.group(1)
assert "headSha == $qasha" in JOB_FILTER, "The actual execution SHA must be revalidated"

# Extract the actual GitHub REST child-run identity expression rather than simulating it.
identity_start = WORKFLOW.index('          jq -e --arg qasha "$QA_SHA" --arg title "$EXPECTED_TITLE"')
identity_end = WORKFLOW.index('          \' <<< "$RUN_DETAILS" >/dev/null', identity_start)
identity_block = WORKFLOW[identity_start:identity_end]
assert identity_block.count("'") == 1, "Identity predicate must begin with one quote"
IDENTITY_FILTER = identity_block.split("'", 1)[1]
for token in (".event ==", ".head_sha == $qasha", ".workflow_id == $workflow_id",
              ".path == $wf", ".display_title == $title", ".created_at >= $after"):
    assert token in IDENTITY_FILTER, f"Identity check missing {token}"

def jq(expr, payload, variables=None, exit_on_false=False):
    args = ["jq", "-er" if exit_on_false else "-r"]
    for name, value in (variables or {}).items():
        if name == "workflow_id":
            args += ["--argjson", name, str(value)]
        else:
            args += ["--arg", name, str(value)]
    return subprocess.run(args + [expr], input=json.dumps(payload),
                          capture_output=True, text=True, check=False)

def run_case(name, expr, payload, variables, expected, exit_on_false=False):
    actual = jq(expr, payload, variables, exit_on_false)
    got = actual.stdout.strip()
    passed = (actual.returncode == 0 and got == (str(expected).lower() if isinstance(expected,bool) else expected))
    if not expected and exit_on_false:
        passed = actual.returncode != 0
    assert passed, (name, actual.returncode, got, actual.stderr)
    print("PASS:", name)

def child(rid, title=TITLE, when=FRESH, branch="main", sha=QA_SHA):
    return {"databaseId":rid, "displayTitle":title,"createdAt":when,
            "headBranch":branch,"headSha":sha}

run_vars = {"title":TITLE,"qasha":QA_SHA,"after":BOUNDARY}
for label, runs, expected in [
    ("valid exact child", [child(100)], "100"),
    ("stale/replayed child rejected", [child(99,when=STALE)], ""),
    ("wrong source QA SHA rejected", [child(99,sha=OTHER_SHA)], ""),
    ("wrong product SHA in title rejected", [child(99,title=f"INT-REG02A {REQUEST} / {OTHER_SHA}")], ""),
    ("request suffix collision rejected", [child(99,title=f"INT-REG02A {REQUEST}0 / {APP_SHA}")], ""),
    ("unrelated title prefix rejected", [child(99,title=f"prefix {TITLE}")], ""),
    ("wrong child branch rejected", [child(99,branch="feature/review")], ""),
    ("missing child rejected", [], ""),
    ("duplicate matching children rejected", [child(98),child(99)], ""),
    ("single valid child amid unrelated runs selected", [child(97,sha=OTHER_SHA),
                                                         child(98,when=STALE),child(100)], "100"),
]:
    run_case(label,RUN_FILTER,runs,run_vars,expected)

identity_vars = {"qasha":QA_SHA,"title":TITLE,"wf":WF_PATH,
                 "after":BOUNDARY,"workflow_id":WF_ID}
identity_valid = {"event":"workflow_dispatch","head_branch":"main","head_sha":QA_SHA,
                  "workflow_id":WF_ID,"path":WF_PATH,"display_title":TITLE,
                  "created_at":FRESH}
run_case("exact workflow ID/path/event/head SHA accepted",IDENTITY_FILTER,identity_valid,identity_vars,True,True)
for label, field, value in [
    ("wrong event rejected","event","push"),
    ("wrong workflow ID rejected","workflow_id",WF_ID+1),
    ("wrong workflow path rejected","path",".github/workflows/unapproved.yml"),
    ("wrong QA SHA rejected","head_sha",OTHER_SHA),
    ("wrong title rejected","display_title","prefix "+TITLE),
    ("wrong branch rejected","head_branch","feature/test"),
    ("stale run rejected","created_at",STALE),
]:
    mutated = {**identity_valid,field:value}
    run_case(label,IDENTITY_FILTER,mutated,identity_vars,False,True)

def job(name, conclusion="success"):
    return {"name":name,"conclusion":conclusion}

old_guard=job("Check approved source pins and disposable-only gate")
old_backend=job("Backend full regression + disposable PostgreSQL")
old_frontend=job("Independent frozen Reception/Appointment baseline")
new_guard=job("Check reviewed plan and exact synthetic PR source")
new_frontend=job("Pinned frontend build, contract, model and Playwright QA")
def completed(jobs,status="completed",conclusion="success",sha=QA_SHA):
    return {"status":status,"conclusion":conclusion,"headSha":sha,"jobs":jobs}

for label, workflow, payload, expected in [
    ("original INTREG01 valid", "qa-int-reg01.yml", completed([old_guard,old_backend,old_frontend]),True),
    ("new INTREG02A valid", "qa-int-reg02a.yml",completed([new_guard,new_frontend]),True),
    ("REG02A missing frontend", "qa-int-reg02a.yml",completed([new_guard]),False),
    ("REG02A skipped guard", "qa-int-reg02a.yml",completed([job(new_guard["name"],"skipped"),new_frontend]),False),
    ("REG02A failed frontend", "qa-int-reg02a.yml",completed([new_guard,job(new_frontend["name"],"failure")]),False),
    ("REG02A cancelled", "qa-int-reg02a.yml",completed([new_guard,new_frontend],conclusion="cancelled"),False),
    ("REG02A still running", "qa-int-reg02a.yml",completed([new_guard,new_frontend],status="in_progress"),False),
    ("REG02A wrong QA SHA", "qa-int-reg02a.yml",completed([new_guard,new_frontend],sha=OTHER_SHA),False),
    ("REG02A duplicate names", "qa-int-reg02a.yml",completed([new_guard,new_frontend,new_frontend]),False),
    ("REG02A extra job", "qa-int-reg02a.yml",completed([new_guard,new_frontend,job("Other job")]),False),
    ("REG02A misleading job name", "qa-int-reg02a.yml",completed([new_guard,job(new_frontend["name"]+" forged")]),False),
    ("old INTREG01 missing backend", "qa-int-reg01.yml",completed([old_guard,old_frontend]),False),
    ("old INTREG01 skipped backend", "qa-int-reg01.yml",completed([old_guard,job(old_backend["name"],"skipped"),old_frontend]),False),
    ("old workflow with new jobs", "qa-int-reg01.yml",completed([new_guard,new_frontend]),False),
    ("arbitrary workflow rejected", "qa-arbitrary.yml",completed([old_guard,old_backend,old_frontend]),False),
]:
    run_case(label,JOB_FILTER,payload,{"workflow":workflow,"qasha":QA_SHA},expected,True)
print("PASS: 10 child-correlation, 8 identity and 15 workflow-result cases.")
