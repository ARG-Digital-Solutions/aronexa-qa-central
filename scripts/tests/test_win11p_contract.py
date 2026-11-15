import copy
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from win11p_contract import (
    GATES, validate_plan, validate_context, validate_scope, junit_counts,
    validate_evidence, validate_receipt, read_artifact, validate_artifact_metadata,
)

ROOT = Path(__file__).resolve().parents[2]
SHA = "a" * 40
QA = "b" * 40
DIGEST = "c" * 64

def counts(n):
    return dict(tests=n, failures=0, errors=0, skipped=0)

def evidence():
    return dict(schema_version=1, plan_id="WIN11P_RECEPTION_E2E",
        source_sha=SHA, qa_sha=QA, request_id="123-1", run_id="123", run_attempt="1",
        source_bundle_sha256=DIGEST, qa_archive_sha256=DIGEST,
        source_clean=True, versions=dict(java=21, node=24, postgres=17),
        gates={key:"PASS" for key in GATES}, frontend=counts(249),
        search=counts(7), roles=counts(4), rls=counts(8), phase_a=counts(1), phase_b=counts(1),
        full_maven={**counts(1), "exit_code":0},
        operator={**counts(1), "patients":1, "checked_in":1},
        pids=dict(a=101,b=202), database_run_id="11111111-1111-4111-8111-111111111111",
        operator_database_run_id="22222222-2222-4222-8222-222222222222", database_identity_verified=True, portable_identity_verified=True,
        portable_runtime_sha256=DIGEST, classification="NOT_READY", release_authorized=False)

def source_pr(plan):
    return dict(number=148, state="open", draft=True, user=dict(login="author"),
        head=dict(sha=plan["source_expected_head_sha"], ref=plan["source_branch"],
                  repo=dict(full_name=plan["source_repository"])),
        base=dict(ref=plan["source_base_branch"],sha=plan["source_baseline_sha"]))

def context(plan):
    return dict(event="workflow_dispatch", ref="refs/heads/main", qa_sha=QA,
        authorized_qa_sha=QA, source_sha=plan["source_expected_head_sha"],
        acknowledgement=True, runner_approved=True, reviewer="independent",
        operator="operator", reviewed_qa_sha=QA, run_id="123", run_attempt="1")

class ContractTests(unittest.TestCase):
    def setUp(self):
        self.plan=json.loads((ROOT/"qa/plans/WIN11P_RECEPTION_E2E.json").read_text())
        self.plan["qa_workflow"]="qa-win11p-reception.yml"
        self.legacy=json.loads((ROOT/"qa/plans/P01_T07_INT_REG_01.json").read_text())

    def test_complete_win_plan_is_structural_only(self):
        validate_plan(self.plan,ROOT)
        self.assertEqual(self.plan["status"],"DRAFT_NOT_ACTIVATED")
        self.assertEqual(self.plan["disposition"],"NOT_RUN")
    def test_legacy_valid_without_win_gates(self):
        validate_plan(self.legacy, ROOT)
    def test_legacy_requires_original_workflow_and_checks(self):
        for field,value in [("qa_workflow","qa-win11p-reception.yml"),("required_checks",[])]:
            p=copy.deepcopy(self.legacy);p[field]=value
            with self.assertRaises(ValueError): validate_plan(p,ROOT)
    def test_unknown_plan_rejected(self):
        p=copy.deepcopy(self.plan);p["plan_id"]="UNREGISTERED_PLAN"
        with self.assertRaises(ValueError): validate_plan(p,ROOT)
    def test_win_requires_all_eight_original_gates(self):
        for gate in GATES:
            p=copy.deepcopy(self.plan);p["required_checks"].remove(gate)
            with self.assertRaises(ValueError): validate_plan(p,ROOT)
    def test_win_requires_reviewed_schema2_inventory_pin(self):
        for field,value in (("required_evidence_schema_version",1),("required_evidence_schema_version",None),
                            ("expected_inventory_sha256",""),("expected_inventory_sha256",None)):
            p=copy.deepcopy(self.plan);p[field]=value
            with self.subTest(field=field,value=value),self.assertRaises(ValueError):validate_plan(p,ROOT)
    def test_win_cannot_route_to_int_reg01(self):
        p=copy.deepcopy(self.plan);p["qa_workflow"]="qa-int-reg01.yml"
        with self.assertRaises(ValueError): validate_plan(p,ROOT)
    def test_scope_exact_no_wildcards_or_traversal(self):
        validate_scope(self.plan,self.plan["authorized_changed_paths"])
        for bad in [["backend/extra.java"],self.plan["authorized_changed_paths"]+["extra"]]:
            with self.assertRaises(ValueError):validate_scope(self.plan,bad)
        for bad in ["../secret","/secret","backend/*","C:/secret","a\\b"]:
            p=copy.deepcopy(self.plan);p["authorized_changed_paths"]=[bad]
            with self.assertRaises(ValueError):validate_plan(p,ROOT)
    def test_legacy_release_and_review_guards_retained(self):
        for field,value in [("test_only",False),("independent_review_required",False),
                            ("customer_release_allowed_on_ci_pass",True),("qa_issue_number",True)]:
            p=copy.deepcopy(self.legacy);p[field]=value
            with self.assertRaises(ValueError):validate_plan(p,ROOT)
    def test_context_exact_main_admin_pin_draft(self):
        p=self.plan;c=context(p)
        validate_context(p,source_pr(p),dict(user=dict(login="qa-author")),
            [dict(user=dict(login="independent",type="User"),state="APPROVED",commit_id=QA)],c)
    def test_context_rejects_branch_unapproved_runner_or_missing_ack(self):
        for field,value in [("event","pull_request"),("ref","refs/heads/feature"),
                            ("authorized_qa_sha",""),("runner_approved",False),
                            ("acknowledgement",False),("reviewer",""),("operator","")]:
            c=context(self.plan);c[field]=value
            with self.assertRaises(ValueError):
                validate_context(self.plan,source_pr(self.plan),dict(user=dict(login="qa-author")),[],c)
    def test_context_rejects_stale_fork_wrong_base_or_ready_pr(self):
        for field in ["stale","fork","base","base_sha","ready","closed"]:
            pr=source_pr(self.plan)
            if field=="stale":pr["head"]["sha"]=SHA
            if field=="fork":pr["head"]["repo"]["full_name"]="evil/fork"
            if field=="base":pr["base"]["ref"]="main"
            if field=="base_sha":pr["base"]["sha"]="0"*40
            if field=="ready":pr["draft"]=False
            if field=="closed":pr["state"]="closed"
            with self.assertRaises(ValueError):
                validate_context(self.plan,pr,dict(user=dict(login="qa-author")),[],context(self.plan))
    def test_context_rejects_self_bot_stale_or_dismissed_review(self):
        for login,kind,state,sha in [("author","User","APPROVED",QA),
            ("qa-author","User","APPROVED",QA),("independent","Bot","APPROVED",QA),
            ("independent","User","CHANGES_REQUESTED",QA),("independent","User","APPROVED",SHA)]:
            c=context(self.plan);c["reviewer"]=login
            with self.assertRaises(ValueError):
                validate_context(self.plan,source_pr(self.plan),dict(user=dict(login="qa-author")),
                    [dict(user=dict(login=login,type=kind),state=state,commit_id=sha)],c)
    def test_junit_sanitizes_properties_and_error_text(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"report.xml"
            path.write_text('<testsuite tests="1" failures="0" errors="0" skipped="0">'
                '<properties><property name="password" value="DO_NOT_PUBLISH"/></properties>'
                '<testcase name="expected"/></testsuite>')
            result=junit_counts(path,1,"expected")
            self.assertEqual(result,counts(1))
            self.assertNotIn("DO_NOT_PUBLISH",json.dumps(result))
    def test_junit_rejects_skips_counts_dtd_wrong_method_or_missing(self):
        for xml in ['<testsuite tests="1" failures="0" errors="0" skipped="1"><testcase name="expected"><skipped/></testcase></testsuite>',
            '<testsuite tests="2" failures="0" errors="0" skipped="0"><testcase name="expected"/></testsuite>',
            '<!DOCTYPE x><testsuite/>','<testsuite tests="1" failures="0" errors="0" skipped="0"><testcase name="wrong"/></testsuite>']:
            with tempfile.TemporaryDirectory() as d:
                path=Path(d)/"x.xml";path.write_text(xml)
                with self.assertRaises(ValueError):junit_counts(path,1,"expected")
        with self.assertRaises(ValueError):junit_counts(Path("nonexistent-report"),1)
    def test_complete_evidence_valid(self):
        validate_evidence(evidence(),SHA,QA,"123-1")
    def test_any_missing_skipped_or_failed_gate_rejects(self):
        for gate in GATES:
            for value in ["FAIL","NOT_RUN",None]:
                e=evidence();e["gates"][gate]=value
                with self.assertRaises(ValueError):validate_evidence(e,SHA,QA,"123-1")
    def test_evidence_stale_same_pid_zero_operator_wrong_versions_or_full_failure(self):
        for change in [dict(source_sha=QA),dict(request_id="124-1"),dict(pids=dict(a=101,b=101)),
            dict(operator={**counts(1),"patients":0,"checked_in":0}),
            dict(versions=dict(java=21,node=22,postgres=17)),
            dict(full_maven={**counts(1),"exit_code":1}),
            dict(portable_identity_verified=False),dict(database_identity_verified=False),
            dict(release_authorized=True)]:
            e=evidence();e.update(change)
            with self.assertRaises(ValueError):validate_evidence(e,SHA,QA,"123-1")
    def test_evidence_rejects_extra_data_secret_fields_and_negative_counts(self):
        e=evidence();e["raw_log"]="SECRET"
        with self.assertRaises(ValueError):validate_evidence(e,SHA,QA,"123-1")
        for field in ["frontend","search","phase_a","phase_b"]:
            e=evidence();e[field]["skipped"]=1
            with self.assertRaises(ValueError):validate_evidence(e,SHA,QA,"123-1")
        e=evidence();e["search"]["tests"]=-1
        with self.assertRaises(ValueError):validate_evidence(e,SHA,QA,"123-1")
    def test_artifact_zip_exact_identity_and_no_extra_or_traversal(self):
        for names in [["evidence.json"],["../evidence.json"],["evidence.json","credentials.txt"]]:
            stream=io.BytesIO()
            with zipfile.ZipFile(stream,"w") as z:
                for name in names:z.writestr(name,json.dumps(evidence()))
            data=stream.getvalue();digest=hashlib.sha256(data).hexdigest()
            if names==["evidence.json"]:
                self.assertEqual(read_artifact(data,digest)["source_sha"],SHA)
                with self.assertRaises(ValueError):read_artifact(data,"0"*64)
            else:
                with self.assertRaises(ValueError):read_artifact(data,digest)
    def test_artifact_json_rejects_duplicate_keys_and_nonfinite_numbers(self):
        for content in ('{"schema_version":1,"schema_version":2}','{"tests":NaN}'):
            stream=io.BytesIO()
            with zipfile.ZipFile(stream,"w") as z:z.writestr("evidence.json",content)
            raw=stream.getvalue()
            with self.subTest(content=content),self.assertRaises(ValueError):read_artifact(raw,hashlib.sha256(raw).hexdigest())
    def test_artifact_api_requires_current_run_name_sha_and_digest(self):
        m=dict(id=12,name="win11p-evidence-123-1",expired=False,digest="sha256:"+DIGEST,
            workflow_run=dict(id=123,head_sha=QA))
        validate_artifact_metadata(m,"123","1",QA,12,DIGEST)
        for field,value in [("expired",True),("digest","sha256:"+"0"*64),("name","other")]:
            bad=copy.deepcopy(m);bad[field]=value
            with self.assertRaises(ValueError):validate_artifact_metadata(bad,"123","1",QA,12,DIGEST)
    def test_receipt_must_be_independent_exact_and_artifact_bound(self):
        e=evidence()
        r=dict(plan_id=e["plan_id"],source_sha=SHA,qa_sha=QA,request_id="123-1",
            run_id="123",run_attempt="1",artifact_id=12,evidence_sha256=DIGEST,
            disposition="PASS",operator_workflow_confirmed=True)
        validate_receipt(r,"independent","User","independent","author","qa-author",e,12,DIGEST)
        for key,value in [("source_sha",QA),("artifact_id",13),("evidence_sha256","0"*64),
                          ("disposition","NOT_RUN"),("operator_workflow_confirmed",False)]:
            bad=copy.deepcopy(r);bad[key]=value
            with self.assertRaises(ValueError):
                validate_receipt(bad,"independent","User","independent","author","qa-author",e,12,DIGEST)
        with self.assertRaises(ValueError):
            validate_receipt(r,"author","User","author","author","qa-author",e,12,DIGEST)

if __name__=="__main__":unittest.main()
