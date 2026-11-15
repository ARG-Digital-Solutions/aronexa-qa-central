"""Pure fail-closed contracts for the manual WIN11P proposal. No network or execution."""
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import uuid
import xml.etree.ElementTree as ET
import zipfile

REPOSITORY = "ARG-Digital-Solutions/aronexa-healthcare-platform"
PLAN = "WIN11P_RECEPTION_E2E"
GATES = (
    "exact_source_sha_and_clean_checkout",
    "portable_java21_actual_forked_jvm_identity",
    "frontend_model_regression_and_connected_build",
    "real_http_pg17_tenant_branch_staff_session_rls_negatives",
    "chromium_login_search_registration_booking_checkin_daily_queue",
    "same_marked_database_distinct_backend_process_restart",
    "operator_workflow_on_connected_frontend",
    "full_maven_failures_preserved",
)
LEGACY_CHECKS = {"maven_verify_and_testcontainers", "verified_playwright"}
WORKFLOWS = {"P01_T07_INT_REG_01":"qa-int-reg01.yml", PLAN:"qa-win11p-reception.yml"}
COUNT_KEYS = {"tests", "failures", "errors", "skipped"}

def require(condition, reason):
    if not condition:
        raise ValueError(reason)

def sha(value, size=40):
    return isinstance(value,str) and re.fullmatch("[0-9a-f]{%d}" % size,value) is not None

def number(value, minimum=0):
    return type(value) is int and minimum <= value <= 1000000

def validate_plan(data, root):
    pid=data.get("plan_id")
    require(pid in WORKFLOWS, "unknown plan")
    require(data.get("source_repository")==REPOSITORY, "wrong source repository")
    require(data.get("qa_workflow")==WORKFLOWS[pid], "unknown plan/workflow pair")
    for key in ("source_baseline_sha","frozen_frontend_sha"):
        require(sha(data.get(key)), "invalid source pin")
    for key in ("source_base_branch","task_id"):
        require(isinstance(data.get(key),str) and data[key].strip(), "missing plan metadata")
    paths=data.get("authorized_changed_paths")
    require(isinstance(paths,list) and paths and all(isinstance(p,str) for p in paths), "missing paths")
    require(len(paths)==len(set(paths)), "duplicate paths")
    for p in paths:
        require(p and not p.startswith("/") and not any(c in p for c in "*?[]\\:")
                and ".." not in PurePosixPath(p).parts, "unsafe path")
    checks=data.get("required_checks")
    require(isinstance(checks,list) and all(isinstance(c,str) for c in checks), "missing checks")
    if pid=="P01_T07_INT_REG_01":
        require(LEGACY_CHECKS.issubset(set(checks)), "legacy checks missing")
    else:
        require(tuple(checks)==GATES, "WIN11P original eight checks changed")
        require(sha(data.get("source_expected_head_sha")), "missing current head pin")
        require(data["frozen_frontend_sha"]==data["source_expected_head_sha"], "frontend/source mismatch")
        require(data.get("source_pr_number")==148 and data.get("qa_issue_number")==38, "wrong task")
        require(data.get("approved_alternate_preview_port")==5186 and data.get("default_preview_port")==5176,
                "port contract changed")
        require(data.get("status")=="DRAFT_NOT_ACTIVATED" and data.get("disposition")=="NOT_RUN",
                "static plan cannot approve execution")
    require(type(data.get("qa_issue_number")) is int and data["qa_issue_number"]>0, "missing QA issue")
    require(data.get("test_only") is True and data.get("independent_review_required") is True,
            "review/test-only gate weakened")
    require(data.get("customer_release_allowed_on_ci_pass") is False, "release gate weakened")
    require((Path(root)/".github/workflows"/data["qa_workflow"]).is_file(), "workflow absent")

def validate_scope(plan, changed):
    require(isinstance(changed,list) and len(changed)==len(set(changed))
            and set(changed)==set(plan["authorized_changed_paths"]), "source scope mismatch")

def validate_context(plan, pr, qa_pr, reviews, context):
    require(context.get("event")=="workflow_dispatch" and context.get("ref")=="refs/heads/main",
            "manual trusted-main execution only")
    require(sha(context.get("qa_sha")) and context["qa_sha"]==context.get("authorized_qa_sha"),
            "QA revision not explicitly authorized")
    require(context.get("acknowledgement") is True and context.get("runner_approved") is True,
            "disposable runner not authorized")
    require(context.get("source_sha")==plan["source_expected_head_sha"], "unreviewed source SHA")
    require(pr.get("number")==148 and pr.get("state")=="open" and pr.get("draft") is True,
            "exact open draft PR required")
    require(pr.get("head",{}).get("sha")==context["source_sha"] and
            pr["head"].get("ref")==plan["source_branch"] and
            pr["head"].get("repo",{}).get("full_name")==REPOSITORY and
            pr.get("base",{}).get("ref")==plan["source_base_branch"], "stale/fork/base mismatch")
    reviewer=context.get("reviewer")
    operator=context.get("operator")
    require(isinstance(reviewer,str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]{0,38}",reviewer),
            "independent reviewer not configured")
    require(isinstance(operator,str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]{0,38}",operator),
            "operator not configured")
    authors={pr.get("user",{}).get("login","").lower(),qa_pr.get("user",{}).get("login","").lower()}
    require(reviewer.lower() not in authors and operator.lower() not in authors,
            "independent review/operator cannot be implementation author")
    require(sha(context.get("reviewed_qa_sha")), "review revision missing")
    selected=[r for r in reviews if r.get("user",{}).get("login","").lower()==reviewer.lower()]
    require(selected and selected[-1].get("state")=="APPROVED" and
            selected[-1].get("commit_id")==context["reviewed_qa_sha"] and
            selected[-1].get("user",{}).get("type")=="User", "current independent approval absent")
    require(str(context.get("run_id","")).isdigit() and int(context["run_id"])>0 and
            str(context.get("run_attempt","")).isdigit() and int(context["run_attempt"])>0, "run identity missing")

def xml_root(path):
    try:
        raw=Path(path).read_bytes()
        require(len(raw)<=8*1024*1024 and b"<!DOCTYPE" not in raw.upper()
                and b"<!ENTITY" not in raw.upper(), "unsafe XML")
        return ET.fromstring(raw)
    except (OSError,ET.ParseError) as exc:
        raise ValueError("missing or malformed JUnit") from exc

def junit_counts(path, minimum, method=None):
    root=xml_root(path)
    require(root.tag=="testsuite", "unexpected JUnit root")
    try:
        out={k:int(root.attrib[k]) for k in COUNT_KEYS}
    except (KeyError,ValueError) as exc:
        raise ValueError("JUnit count metadata missing") from exc
    cases=root.findall("testcase")
    require(all(number(n) for n in out.values()) and out["tests"]==len(cases), "JUnit count mismatch")
    require(out["tests"]>=minimum and not any(out[k] for k in ("failures","errors","skipped")),
            "JUnit failed/skipped/empty")
    require(not any(c.find(tag) is not None for c in cases for tag in ("failure","error","skipped")),
            "JUnit case failed/skipped")
    if method:
        require(len(cases)==1 and cases[0].get("name")==method, "wrong JUnit method")
    return out

def validate_counts(value, minimum, extras=frozenset()):
    require(isinstance(value,dict) and set(value)==COUNT_KEYS|set(extras), "unexpected count fields")
    require(all(number(value[k]) for k in COUNT_KEYS), "invalid counts")
    require(value["tests"]>=minimum and not any(value[k] for k in ("failures","errors","skipped")),
            "missing/failed/skipped tests")

def validate_evidence(data, source_sha, qa_sha, request):
    fields={"schema_version","plan_id","source_sha","qa_sha","request_id","run_id","run_attempt",
        "source_bundle_sha256","qa_archive_sha256","source_clean","versions","gates","frontend",
        "search","roles","rls","phase_a","phase_b","full_maven","operator","pids","database_run_id",
        "operator_database_run_id","database_identity_verified","portable_identity_verified","portable_runtime_sha256",
        "classification","release_authorized"}
    require(isinstance(data,dict) and set(data)==fields, "unexpected evidence fields")
    require(type(data["schema_version"]) is int and data["schema_version"]==1 and data["plan_id"]==PLAN, "wrong evidence schema/plan")
    require(sha(source_sha) and sha(qa_sha) and data["source_sha"]==source_sha
            and data["qa_sha"]==qa_sha and data["request_id"]==request, "stale evidence")
    require(re.fullmatch(r"[1-9][0-9]*-[1-9][0-9]*",request) is not None and
            request==str(data["run_id"])+"-"+str(data["run_attempt"]), "request/run mismatch")
    require(data["source_clean"] is True and data["release_authorized"] is False
            and data["classification"]=="NOT_READY", "source/release gate mismatch")
    require(data["versions"]==dict(java=21,node=24,postgres=17), "wrong toolchain")
    require(isinstance(data["gates"],dict) and set(data["gates"])==set(GATES)
            and all(v=="PASS" for v in data["gates"].values()), "required gate unexecuted/failed")
    for key,minimum in (("frontend",249),("search",7),("roles",4),("rls",8),("phase_a",1),("phase_b",1)):
        validate_counts(data[key],minimum)
    require(data["phase_a"]["tests"]==1 and data["phase_b"]["tests"]==1, "wrong phase count")
    validate_counts(data["full_maven"],1,{"exit_code"})
    require(type(data["full_maven"]["exit_code"]) is int and data["full_maven"]["exit_code"]==0,
            "full Maven did not pass")
    validate_counts(data["operator"],1,{"patients","checked_in"})
    require(data["operator"]["tests"]==1 and number(data["operator"]["patients"],1)
            and number(data["operator"]["checked_in"],1), "operator workflow empty")
    require(isinstance(data["pids"],dict) and set(data["pids"])=={"a","b"}
            and number(data["pids"]["a"],1) and number(data["pids"]["b"],1)
            and data["pids"]["a"]!=data["pids"]["b"], "distinct JVM proof missing")
    try:
        require(str(uuid.UUID(data["database_run_id"]))==data["database_run_id"], "invalid DB marker")
        require(str(uuid.UUID(data["operator_database_run_id"]))==data["operator_database_run_id"]
                and data["operator_database_run_id"]!=data["database_run_id"],"operator DB marker missing/reused")
    except (ValueError,TypeError,AttributeError) as exc:
        raise ValueError("invalid DB marker") from exc
    require(data["database_identity_verified"] is True and data["portable_identity_verified"] is True,
            "database/runtime proof missing")
    for key in ("source_bundle_sha256","qa_archive_sha256","portable_runtime_sha256"):
        require(sha(data[key],64), "artifact identity missing")

def read_artifact(raw, digest):
    require(sha(digest,64) and hashlib.sha256(raw).hexdigest()==digest, "artifact ZIP digest mismatch")
    require(len(raw)<=256*1024, "artifact archive oversized")
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            require(z.namelist()==["evidence.json"] and len(z.infolist())==1, "unexpected artifact entries")
            item=z.infolist()[0]
            require(item.file_size<=65536 and not item.is_dir(), "evidence oversized")
            return json.loads(z.read(item).decode("utf-8"))
    except (zipfile.BadZipFile,UnicodeError,json.JSONDecodeError) as exc:
        raise ValueError("malformed evidence archive") from exc

def validate_artifact_metadata(meta, run_id, attempt, qa_sha, artifact_id, digest):
    require(type(artifact_id) is int and artifact_id>0 and meta.get("id")==artifact_id,
            "artifact ID mismatch")
    require(meta.get("name")=="win11p-evidence-"+str(run_id)+"-"+str(attempt)
            and meta.get("expired") is False and meta.get("digest")=="sha256:"+digest,
            "artifact name/expiry/digest mismatch")
    require(meta.get("workflow_run",{}).get("id")==int(run_id)
            and meta["workflow_run"].get("head_sha")==qa_sha, "artifact from another run/revision")

def validate_receipt(receipt, login, user_type, reviewer, app_author, qa_author, data, artifact_id, digest):
    keys={"plan_id","source_sha","qa_sha","request_id","run_id","run_attempt","artifact_id",
          "evidence_sha256","disposition","operator_workflow_confirmed"}
    require(isinstance(receipt,dict) and set(receipt)==keys, "unexpected review receipt fields")
    require(user_type=="User" and login.lower()==reviewer.lower()
            and login.lower() not in {app_author.lower(),qa_author.lower()}, "receipt not independent")
    require(all(receipt[k]==data[k] for k in ("plan_id","source_sha","qa_sha","request_id","run_id","run_attempt")),
            "receipt is stale")
    require(receipt["artifact_id"]==artifact_id and receipt["evidence_sha256"]==digest
            and receipt["disposition"]=="PASS" and receipt["operator_workflow_confirmed"] is True,
            "review/artifact disposition missing")
