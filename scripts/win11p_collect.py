"""Allowlist-only sanitizer. Reads private local files; publishes no raw logs/XML."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from win11p_contract import GATES,PLAN,COUNT_KEYS,require,xml_root,junit_counts,validate_evidence

def text(path):
    raw=Path(path).read_bytes()
    require(len(raw)<=32*1024*1024,"private log oversized")
    return raw.decode("utf-16" if raw.startswith((b"\xff\xfe",b"\xfe\xff")) else "utf-8-sig")

def read_node_counts(path):
    found={}
    for line in text(path).splitlines():
        m=re.fullmatch(r"(?:[#\u2139]\s*)?(tests|pass|fail|cancelled|skipped)\s+([0-9]+)",line.strip())
        if m:found[m[1]]=int(m[2])
    require(set(found)=={"tests","pass","fail","cancelled","skipped"},"Node counts absent")
    require(found["pass"]==found["tests"] and found["cancelled"]==0,"Node tests incomplete")
    return dict(tests=found["tests"],failures=found["fail"],errors=0,skipped=found["skipped"])

def totals(paths):
    result={key:0 for key in COUNT_KEYS}
    require(paths,"Maven reports absent")
    for path in paths:
        root=xml_root(path)
        require(root.tag=="testsuite","bad Maven report")
        cases=root.findall("testcase")
        declared={key:int(root.attrib[key]) for key in COUNT_KEYS}
        actual={"tests":len(cases),**{key:sum(c.find(tag) is not None for c in cases)
            for key,tag in (("failures","failure"),("errors","error"),("skipped","skipped"))}}
        require(declared==actual and all(v>=0 for v in declared.values()),"inconsistent full Maven counts")
        for key in COUNT_KEYS:result[key]+=declared[key]
    return result

def postgres_observed(path, run_id):
    records=[json.loads(line) for line in text(path).splitlines() if line.strip()]
    selected=[r for r in records if r.get("run_id")==run_id]
    require(len(selected)==1,"missing/ambiguous PostgreSQL observation")
    r=selected[0]
    require(set(r)=={"run_id","version_num","container_id","database_name","loopback"}
        and type(r["version_num"]) is int and 170000<=r["version_num"]<180000
        and re.fullmatch("[0-9a-f]{64}",r["container_id"]) is not None
        and r["database_name"]=="aronexa_pilot05_disposable_only" and r["loopback"] is True,
        "wrong PostgreSQL identity/version")
    return 17

def runtime_hash(root):
    root=Path(root).resolve()
    digest=hashlib.sha256()
    for path in sorted(root.rglob("*")):
        require(not path.is_symlink(),"portable runtime symlink refused")
        if path.is_file():
            item=hashlib.sha256(path.read_bytes()).hexdigest()
            digest.update((path.relative_to(root).as_posix()+"\0"+item+"\n").encode("utf-8"))
    return digest.hexdigest()

def portable_xml(path, home):
    root=xml_root(path)
    actual=[p.get("value") for p in root.findall("./properties/property") if p.get("name")=="java.home"]
    require(len(actual)==1 and Path(actual[0]).resolve()==Path(home).resolve(),"portable JVM identity mismatch")
    versions=[p.get("value") for p in root.findall("./properties/property") if p.get("name")=="java.version"]
    require(len(versions)==1 and re.match(r"21\.",versions[0]) is not None,"portable Java21 required")

def parse_marker(path):
    rows={}
    for line in text(path).splitlines():
        if "=" in line:
            key,value=line.split("=",1);require(key not in rows,"duplicate evidence key");rows[key]=value
    return rows

def collect(descriptor):
    d=json.loads(Path(descriptor).read_text(encoding="utf-8-sig"));c=d["context"]
    zero=dict(tests=0,failures=0,errors=0,skipped=0)
    e=dict(schema_version=1,plan_id=PLAN,source_sha=c["source_sha"],qa_sha=c["qa_sha"],
        request_id=c["request_id"],run_id=c["run_id"],run_attempt=c["run_attempt"],
        source_bundle_sha256=c["source_bundle_sha256"],qa_archive_sha256=c["qa_archive_sha256"],
        source_clean=d.get("source_clean") is True,versions=d["versions"],
        gates={k:"NOT_RUN" for k in GATES},frontend=zero.copy(),search=zero.copy(),roles=zero.copy(),rls=zero.copy(),
        phase_a=zero.copy(),phase_b=zero.copy(),full_maven={**zero,"exit_code":d.get("full_maven_exit",1)},
        operator={**zero,"patients":0,"checked_in":0},pids=dict(a=0,b=0),
        database_run_id="",operator_database_run_id="",database_identity_verified=False,portable_identity_verified=False,
        portable_runtime_sha256="0"*64,classification="NOT_READY",release_authorized=False)
    def attempt(keys,fn):
        try:
            fn()
            for key in keys:e["gates"][key]="PASS"
        except (ValueError,OSError,KeyError,TypeError):
            for key in keys:e["gates"][key]="FAIL"
    if e["source_clean"]:e["gates"][GATES[0]]="PASS"
    def frontend():
        e["frontend"]=read_node_counts(d["frontend_log"])
        require(e["frontend"]["tests"]>=249 and d["frontend_exit"]==0 and d["build_exit"]==0,"frontend incomplete")
        require(not e["frontend"]["failures"] and not e["frontend"]["skipped"],"frontend failed")
    attempt([GATES[2]],frontend)
    def search():
        e["search"]=junit_counts(d["search_xml"],7)
        e["roles"]=junit_counts(d["roles_xml"],4)
        e["rls"]=junit_counts(d["rls_xml"],8)
    attempt([GATES[3]],search)
    def rc03():
        e["phase_a"]=junit_counts(d["phase_a_xml"],1,"phaseARc03BrowserCreatesRegistrationBookingAndCheckIn")
        e["phase_b"]=junit_counts(d["phase_b_xml"],1,"phaseBRc03RecoversBrowserCreatedPatientAndCheckedInQueue")
        marker=parse_marker(d["rc03_summary"])
        require(d["rc03_exit"]==0 and marker["SourceCommit"]==c["source_sha"]
            and marker["Rc03PreviewPort"]=="5186"
            and all(marker[k]=="true" for k in ("Rc03BrowserCreatedRegistration",
                "Rc03BrowserCreatedBookingAndCheckIn","Rc03DuplicateRegistrationDenied",
                "Rc03SameMarkedPG17RecoveredDifferentJvm")),"RC03 marker mismatch")
        log=text(d["rc03_log"])
        for key,label in (("a","A"),("b","B")):
            matches=re.findall(r"(?m)^PILOT08_RC03_PHASE_"+label+r"_PID=([1-9][0-9]*)\s*$",log)
            require(len(matches)==1,"missing/duplicate PID");e["pids"][key]=int(matches[0])
        require(e["pids"]["a"]!=e["pids"]["b"],"same JVM reused")
        e["database_run_id"]=marker["RunId"]
        e["versions"]["postgres"]=postgres_observed(d["postgres_observations"],marker["RunId"])
        e["database_identity_verified"]=True
    attempt([GATES[4],GATES[5]],rc03)
    def portable():
        portable_xml(d["phase_a_xml"],d["runtime_home"])
        portable_xml(d["phase_b_xml"],d["runtime_home"])
        value=runtime_hash(d["runtime_home"])
        require(value==d["runtime_sha256"],"runtime changed after build")
        e["portable_runtime_sha256"]=value;e["portable_identity_verified"]=True
    attempt([GATES[1]],portable)
    def operator():
        observation=parse_marker(d["operator_observation"])
        marker=parse_marker(d["operator_summary"])
        require(marker["SourceCommit"]==c["source_sha"],"operator source mismatch")
        postgres_observed(d["postgres_observations"],marker["RunId"])
        e["operator_database_run_id"]=marker["RunId"]
        e["operator"]={**junit_counts(d["operator_xml"],1,"pilot09OperatorAssistedWindowsFictionalLab"),
            "patients":int(observation["PatientRecordsCreated"]),
            "checked_in":int(observation["CheckedInAppointments"])}
        require(d["operator_exit"]==0 and e["operator"]["patients"]>0
                and e["operator"]["checked_in"]>0,"empty operator session")
    attempt([GATES[6]],operator)
    def maven():
        e["full_maven"]={**totals(d["full_maven_reports"]),"exit_code":d["full_maven_exit"]}
        require(e["full_maven"]["tests"]>0 and e["full_maven"]["exit_code"]==0
                and all(e["full_maven"][k]==0 for k in ("failures","errors","skipped")),
                "full Maven failed/skipped; failure counts retained")
    attempt([GATES[7]],maven)
    return e

def main():
    p=argparse.ArgumentParser();p.add_argument("--descriptor",required=True);p.add_argument("--output",required=True)
    a=p.parse_args()
    try:
        evidence=collect(a.descriptor)
        Path(a.output).write_text(json.dumps(evidence,sort_keys=True,indent=2)+"\n",encoding="utf-8")
        validate_evidence(evidence,evidence["source_sha"],evidence["qa_sha"],evidence["request_id"])
    except (ValueError,OSError,KeyError,TypeError):
        print("WIN11P sanitized evidence is incomplete or failed; no PASS",file=sys.stderr)
        return 1
    print("WIN11P sanitized automated evidence complete; independent receipts still required")
    return 0

if __name__=="__main__":raise SystemExit(main())
