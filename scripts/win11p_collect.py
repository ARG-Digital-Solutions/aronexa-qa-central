"""Allowlist-only sanitizer. Reads private local files; publishes no raw logs/XML."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from win11p_contract import (GATES,PLAN,COUNT_KEYS,LANES,OUTCOMES,require,xml_root,junit_counts,
    validate_evidence,canonical_digest,method_digest,sha,number,strict_json_loads)

def normalize_matrix(raw,source_sha,request):
    """Copy only bounded enums, counts and hashed identities from private coordinator data."""
    issues=[]
    if not isinstance(raw,dict):raw={};issues.append("MISSING_MATRIX")
    def integer(value):return value if type(value) is int and -1<=value<=1000000 else -1
    def enum(value,allowed):return value if isinstance(value,str) and value in allowed else "INVALID"
    def rows(key):
        value=raw.get(key)
        if not isinstance(value,list) or len(value)>1000:issues.append("INVALID_"+key.upper());return []
        return value
    def hashed(value):
        if not isinstance(value,str) or not value or len(value)>4096:
            issues.append("INVALID_IDENTITY");return ""
        return hashlib.sha256(value.encode("utf-8")).hexdigest()
    inventory=[]
    for row in rows("inventory"):
        try:
            require(isinstance(row,dict),"bad inventory")
            tags=row["tags"];require(isinstance(tags,list) and len(tags)<=1,"bad tags")
            inventory.append(dict(id_sha256=method_digest(row["id"]),
                tags=sorted(enum(t,{"win11p-"+l for l in LANES if l!="ordinary"}) for t in tags)))
        except (ValueError,KeyError,TypeError):issues.append("INVALID_INVENTORY_ROW")
    inventory.sort(key=lambda r:r["id_sha256"])
    results=[]
    for row in rows("method_results"):
        try:
            require(isinstance(row,dict),"bad method")
            results.append(dict(id_sha256=method_digest(row["id"]),lane=enum(row.get("lane"),set(LANES)),
                                outcome=enum(row.get("outcome"),OUTCOMES)))
        except (ValueError,KeyError,TypeError):issues.append("INVALID_METHOD_ROW")
    results.sort(key=lambda r:(r["id_sha256"],r["lane"],r["outcome"]))
    lanes=[]
    for row in rows("lane_results"):
        if not isinstance(row,dict):issues.append("INVALID_LANE_ROW");continue
        parser=row.get("parser_issues")
        lanes.append(dict(lane=enum(row.get("lane"),set(LANES)),status=enum(row.get("status"),{"PASS","NOT_PASS","NOT_RUN"}),
            exit_code=row.get("exit_code") if type(row.get("exit_code")) is int else None,
            **{k:integer(row.get(k)) for k in COUNT_KEYS|{"not_run","expected_methods"}},
            parser_issue_count=len(parser) if isinstance(parser,list) and len(parser)<=1000 else -1,
            timed_out=row.get("timed_out") is not False))
    lanes.sort(key=lambda r:LANES.index(r["lane"]) if r["lane"] in LANES else len(LANES))
    resources=[]
    for row in rows("resource_observations"):
        if not isinstance(row,dict):issues.append("INVALID_RESOURCE_ROW");continue
        resources.append({**{key+"_sha256":hashed(row.get(key)) for key in
            ("purpose","run_id","container_id","container_name","database_name")},
            "port":integer(row.get("port")),"server_version":integer(row.get("server_version")),
            "image_id":row.get("image_id") if isinstance(row.get("image_id"),str) and
                re.fullmatch(r"sha256:[0-9a-f]{64}",row["image_id"]) else "",
            "loopback":row.get("loopback") is True,
            "cleanup_status":enum(row.get("cleanup_status"),{"PASS","NOT_PASS","NOT_RUN"})})
    cleanup=[]
    for row in rows("cleanup_observations"):
        if not isinstance(row,dict):issues.append("INVALID_CLEANUP_ROW");continue
        cleanup.append(dict(purpose_sha256=hashed(row.get("purpose")),run_id_sha256=hashed(row.get("run_id")),
            phase=enum(row.get("phase"),{"recovery_before","finally","recovery_after"}),
            status=enum(row.get("status"),{"PASS","NOT_PASS","NOT_RUN"})))
    teardown=dict(resource_observations=resources,cleanup_observations=cleanup)
    teardown["sha256"]=canonical_digest(teardown)
    bound=raw.get("source_sha")==source_sha and raw.get("request_id")==request and raw.get("schema_version")==2
    if not bound:issues.append("STALE_MATRIX_BINDING")
    parser=raw.get("matrix_issues")
    return dict(execution_run_id=raw.get("run_id") if sha(raw.get("run_id"),32) else "",
        source_sha=raw.get("source_sha") if sha(raw.get("source_sha")) else "",
        request_id=raw.get("request_id") if isinstance(raw.get("request_id"),str) and
            re.fullmatch(r"[1-9][0-9]*-[1-9][0-9]*",raw["request_id"]) else "",
        mode=enum(raw.get("mode"),{"All","Ordinary"}),inventory=inventory,inventory_sha256=canonical_digest(inventory),
        method_results=results,method_results_sha256=canonical_digest(results),lane_results=lanes,
        lane_results_sha256=canonical_digest(lanes),counts={key:integer(raw.get(key)) for key in
            ("inventory_methods","executed_methods","ordinary_expected_methods","guarded_methods_not_run")},
        matrix_overall=enum(raw.get("matrix_overall"),{"PASS","NOT_PASS","NOT_RUN"}),
        matrix_exit_code=integer(raw.get("matrix_exit_code")),
        parser_issue_count=len(parser) if isinstance(parser,list) and len(parser)<=1000 else -1,
        cleanup_status=enum(raw.get("cleanup_status"),{"PASS","NOT_PASS","NOT_RUN"}),
        encrypted_recovery=enum(raw.get("encrypted_recovery"),{"IMPLEMENTED_AND_VERIFIED","NOT_IMPLEMENTED_IN_EXISTING_TEST"}),
        full_verification=enum(raw.get("full_verification"),{"PASS","NOT_PASS","NOT_RUN"}),
        source_binding_verified=bound,xml_verified=False,validation_issues=sorted(set(issues)),teardown=teardown)

def verify_matrix_xml(raw,groups,source_sha,request):
    """Independently reconcile private Surefire cases and bindings with coordinator rows."""
    require(isinstance(raw,dict) and raw.get("schema_version")==2 and raw.get("source_sha")==source_sha
            and raw.get("request_id")==request and sha(raw.get("run_id"),32),"matrix binding mismatch")
    require(isinstance(groups,list) and len(groups)==10 and all(isinstance(g,dict) for g in groups)
            and {g.get("lane") for g in groups}==set(LANES),"matrix report groups missing/duplicate")
    all_rows=[];seen=set();seen_paths=set()
    for group in groups:
        lane=group["lane"];paths=group.get("paths")
        require(isinstance(paths,list) and len(paths)<=500,"invalid report paths")
        actual={k:0 for k in COUNT_KEYS}
        rows=[]
        for path in paths:
            resolved=str(Path(path).resolve())
            require(resolved not in seen_paths,"duplicate report path");seen_paths.add(resolved)
            root=xml_root(path);require(root.tag=="testsuite","unexpected report root")
            for key,expected in (("win11p.run.id",raw["run_id"]),("win11p.source.sha",source_sha),("win11p.lane",lane)):
                values=[p.get("value") for p in root.findall("./properties/property") if p.get("name")==key]
                require(values==[expected],"stale/ambiguous report binding")
            cases=root.findall("testcase");counts={k:0 for k in COUNT_KEYS};counts["tests"]=len(cases)
            for case in cases:
                identity=str(case.get("classname",""))+"#"+str(case.get("name",""))
                method_digest(identity);require(identity not in seen,"duplicate method report");seen.add(identity)
                found=[tag for tag in ("failure","error","skipped") if case.find(tag) is not None]
                require(len(found)<=1,"ambiguous testcase outcome")
                outcome="PASS"
                if found:
                    outcome={"failure":"FAIL","error":"ERROR","skipped":"SKIPPED"}[found[0]]
                    counts[{"failure":"failures","error":"errors","skipped":"skipped"}[found[0]]]+=1
                rows.append(dict(id=identity,lane=lane,outcome=outcome))
            try:declared={k:int(root.attrib[k]) for k in COUNT_KEYS}
            except (ValueError,KeyError) as exc:raise ValueError("malformed report counters") from exc
            require(declared==counts and all(number(v) for v in declared.values()),"report count mismatch")
            for key in COUNT_KEYS:actual[key]+=counts[key]
        matching=[r for r in raw["lane_results"] if r.get("lane")==lane]
        require(len(matching)==1 and all(matching[0].get(k)==actual[k] for k in COUNT_KEYS),"lane/XML count mismatch")
        declared=[r for r in raw["method_results"] if r.get("lane")==lane and r.get("outcome")!="NOT_RUN"]
        require(sorted(rows,key=lambda r:r["id"])==sorted(declared,key=lambda r:r["id"]),"matrix/XML methods disagree")
        all_rows.extend(rows)
    return all_rows

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

def postgres_observed(path, run_id, resource=None):
    records=[strict_json_loads(line) for line in text(path).splitlines() if line.strip()]
    selected=[r for r in records if r.get("run_id")==run_id]
    require(len(selected)==1,"missing/ambiguous PostgreSQL observation")
    r=selected[0]
    require(set(r)=={"run_id","version_num","container_id","database_name","loopback","image_id"}
        and type(r["version_num"]) is int and 170000<=r["version_num"]<180000
        and re.fullmatch("[0-9a-f]{64}",r["container_id"]) is not None
        and isinstance(r["image_id"],str) and re.fullmatch(r"sha256:[0-9a-f]{64}",r["image_id"]) is not None
        and r["database_name"]=="aronexa_pilot05_disposable_only" and r["loopback"] is True,
        "wrong PostgreSQL identity/version")
    if resource is not None:
        require(resource.get("loopback") is True and r["container_id"]==resource.get("container_id")
                and r["image_id"]==resource.get("image_id")
                and r["version_num"]==resource.get("server_version") and r["database_name"]==resource.get("database_name"),
                "PostgreSQL resource/observer mismatch")
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
    d=strict_json_loads(Path(descriptor).read_text(encoding="utf-8-sig"));c=d["context"]
    zero=dict(tests=0,failures=0,errors=0,skipped=0)
    e=dict(schema_version=2,plan_id=PLAN,source_sha=c["source_sha"],qa_sha=c["qa_sha"],
        request_id=c["request_id"],run_id=c["run_id"],run_attempt=c["run_attempt"],
        source_bundle_sha256=c["source_bundle_sha256"],qa_archive_sha256=c["qa_archive_sha256"],
        source_clean=d.get("source_clean") is True,versions={key:d.get("versions",{}).get(key)
            if type(d.get("versions",{}).get(key)) is int else 0 for key in ("java","node","postgres")},
        gates={k:"NOT_RUN" for k in GATES},frontend=zero.copy(),search=zero.copy(),roles=zero.copy(),rls=zero.copy(),
        phase_a=zero.copy(),phase_b=zero.copy(),full_maven={**zero,"exit_code":d.get("full_maven_exit",1)},
        operator={**zero,"patients":0,"checked_in":0},pids=dict(a=0,b=0),
        database_run_id="",operator_database_run_id="",database_identity_verified=False,portable_identity_verified=False,
        portable_runtime_sha256="0"*64,classification="NOT_READY",release_authorized=False)
    raw={}
    try:
        raw=strict_json_loads(text(d["matrix_results_path"]))
        e["matrix"]=normalize_matrix(raw,c["source_sha"],c["request_id"])
        require(d.get("matrix_execution_run_id")==raw.get("run_id"),"matrix execution run mismatch")
        verify_matrix_xml(raw,d.get("matrix_report_paths"),c["source_sha"],c["request_id"])
        e["matrix"]["xml_verified"]=True
    except (ValueError,OSError,KeyError,TypeError):
        if "matrix" not in e:e["matrix"]=normalize_matrix(raw,c["source_sha"],c["request_id"])
        e["matrix"]["validation_issues"].append("MATRIX_XML_OR_IDENTITY_INVALID")
    def resource_for(purpose,lanes):
        require(e["matrix"]["xml_verified"] is True and e["matrix"]["source_binding_verified"] is True,
                "matrix binding absent")
        found=[r for r in raw["resource_observations"] if r.get("purpose")==purpose]
        require(len(found)==1,"resource identity absent/ambiguous")
        resource=found[0]
        for lane in lanes:
            selected=[r for r in raw["lane_results"] if r.get("lane")==lane]
            require(len(selected)==1 and selected[0].get("resource_run_id")==resource.get("run_id")
                    and selected[0].get("status")=="PASS" and type(selected[0].get("exit_code")) is int
                    and selected[0]["exit_code"]==0,"lane resource binding mismatch")
        postgres_observed(d["postgres_observations"],resource["run_id"],resource)
        return resource
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
        if d.get("rc03_summary"):
            marker=parse_marker(d["rc03_summary"])
            require(d["rc03_exit"]==0 and marker["SourceCommit"]==c["source_sha"]
                and marker["Rc03PreviewPort"]=="5186"
                and all(marker[k]=="true" for k in ("Rc03BrowserCreatedRegistration",
                    "Rc03BrowserCreatedBookingAndCheckIn","Rc03DuplicateRegistrationDenied",
                    "Rc03SameMarkedPG17RecoveredDifferentJvm")),"RC03 marker mismatch")
            run_id=marker["RunId"]
            log=text(d["rc03_log"])
        else:
            lanes=("pilot05-rc03-phase-a","pilot05-rc03-phase-b")
            resource=resource_for("rc03",lanes)
            require(d["rc03_exit"]==0 and all(r.get("preview_port")==5186 for r in raw["lane_results"]
                    if r.get("lane") in lanes),"RC03 preview/source mismatch")
            run_id=resource["run_id"]
            require(isinstance(d.get("rc03_logs"),list) and 1<=len(d["rc03_logs"])<=2,"RC03 logs absent")
            log="\n".join(text(path) for path in d["rc03_logs"])
        for key,label in (("a","A"),("b","B")):
            matches=re.findall(r"(?m)^PILOT08_RC03_PHASE_"+label+r"_PID=([1-9][0-9]*)\s*$",log)
            require(len(matches)==1,"missing/duplicate PID");e["pids"][key]=int(matches[0])
        require(e["pids"]["a"]!=e["pids"]["b"],"same JVM reused")
        e["database_run_id"]=run_id
        e["versions"]["postgres"]=postgres_observed(d["postgres_observations"],run_id)
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
        if d.get("operator_summary"):
            marker=parse_marker(d["operator_summary"])
            require(marker["SourceCommit"]==c["source_sha"],"operator source mismatch")
            run_id=marker["RunId"]
        else:run_id=resource_for("operator",("pilot09-operator",))["run_id"]
        postgres_observed(d["postgres_observations"],run_id)
        e["operator_database_run_id"]=run_id
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
    if not e["matrix"]["xml_verified"]:
        e["gates"][GATES[7]]="FAIL"
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
