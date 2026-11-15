"""Behavioral regressions for complete, source-bound matrix evidence."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parent))
from test_win11p_contract import evidence,SHA,QA
import win11p_contract as contract
import win11p_collect as collector

LANES=("discovery","ordinary","pilot05-phase-a","pilot05-phase-b",
       "pilot05-rc03-phase-a","pilot05-rc03-phase-b","pilot06-browser",
       "pilot07-recovery","pilot07-operator","pilot09-operator")
MATRIX_RUN="0123456789abcdef0123456789abcdef"

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()).hexdigest()

def matrix_fixture():
    inventory=[dict(id="example.OrdinaryTests#case"+str(i),tags=[]) for i in range(343)]
    inventory += [dict(id="example.GuardedTests#"+lane.replace("-","_"),tags=["win11p-"+lane])
                  for lane in LANES if lane!="ordinary"]
    rows=[dict(id=item["id"],lane=(item["tags"][0][7:] if item["tags"] else "ordinary"),outcome="PASS")
          for item in inventory]
    lanes=[dict(lane=lane,status="PASS",exit_code=0,tests=(343 if lane=="ordinary" else 1),
                failures=0,errors=0,skipped=0,not_run=0,expected_methods=(343 if lane=="ordinary" else 1),
                parser_issues=[],timed_out=False) for lane in LANES]
    resources=[dict(purpose=purpose,run_id=str(i)*8+'-'+str(i)*4+'-4'+str(i)*3+'-8'+str(i)*3+'-'+str(i)*12,
                    port=5500+i,container_id=str(i)*64,container_name="synthetic-"+str(i),
                    database_name="aronexa_pilot05_disposable_only",server_version=170011,cleanup_status="PASS",
                    image_id="sha256:"+"f"*64)
               for i,purpose in ((3,"legacy"),(1,"rc03"),(2,"operator"))]
    for resource in resources:resource["loopback"]=True
    cleanup=[dict(purpose=r["purpose"],run_id=r["run_id"],phase="finally",status="PASS") for r in resources]
    return dict(schema_version=2,run_id=MATRIX_RUN,source_sha=SHA,request_id="123-1",mode="All",
                inventory=inventory,method_results=rows,lane_results=lanes,matrix_overall="PASS",matrix_issues=[],
                matrix_exit_code=0,cleanup_status="PASS",encrypted_recovery="IMPLEMENTED_AND_VERIFIED",
                full_verification="PASS",inventory_methods=352,executed_methods=352,ordinary_expected_methods=343,
                guarded_methods_not_run=0,resource_observations=resources,cleanup_observations=cleanup)

def write_matrix_reports(root,raw):
    groups=[]
    for lane in LANES:
        rows=[r for r in raw["method_results"] if r["lane"]==lane and r["outcome"]!="NOT_RUN"]
        cases=''.join('<testcase classname="'+r["id"].split("#")[0]+'" name="'+r["id"].split("#")[1]+'"/>' for r in rows)
        props=''.join('<property name="'+k+'" value="'+v+'"/>' for k,v in
                      (("win11p.run.id",MATRIX_RUN),("win11p.source.sha",SHA),("win11p.lane",lane)))
        path=root/('matrix-'+lane+'.xml')
        path.write_text('<testsuite tests="'+str(len(rows))+'" failures="0" errors="0" skipped="0"><properties>'+props+'</properties>'+cases+'</testsuite>')
        groups.append(dict(lane=lane,paths=[str(path)]))
    return groups

def public_matrix(raw=None):
    """Only collector performs normalization; validation tests mutate its real output."""
    assert hasattr(collector,"normalize_matrix"),"schema2 matrix normalization is required"
    return collector.normalize_matrix(matrix_fixture() if raw is None else raw,SHA,"123-1")

def schema2_evidence():
    e=evidence();e["schema_version"]=2;e["matrix"]=public_matrix()
    e["full_maven"]["tests"]=352
    # XML verification is a private collector observation, never a coordinator claim.
    e["matrix"]["xml_verified"]=True
    return e

class MatrixTests(unittest.TestCase):
    def test_complete_source_bound_matrix_reconciles_all_ten_lanes(self):
        e=schema2_evidence()
        contract.validate_evidence(e,SHA,QA,"123-1",required_schema=2,
                                   expected_inventory_sha256=e["matrix"]["inventory_sha256"])
        self.assertEqual(e["matrix"]["counts"],dict(inventory_methods=352,executed_methods=352,
                         ordinary_expected_methods=343,guarded_methods_not_run=0))
        self.assertEqual(len(e["matrix"]["lane_results"]),10)
        self.assertNotIn("example.",json.dumps(e))

    def test_no_missing_duplicate_unexpected_failed_skipped_or_not_run_method_passes(self):
        for mutation in ("missing","duplicate","unexpected","FAIL","ERROR","SKIPPED","NOT_RUN","wrong_lane"):
            raw=matrix_fixture()
            if mutation=="missing":raw["method_results"].pop()
            elif mutation=="duplicate":raw["method_results"].append(copy.deepcopy(raw["method_results"][0]))
            elif mutation=="unexpected":raw["method_results"][0]["id"]="example.Unknown#unexpected"
            elif mutation=="wrong_lane":raw["method_results"][0]["lane"]="discovery"
            else:raw["method_results"][0]["outcome"]=mutation
            e=evidence();e.update(schema_version=2,matrix=public_matrix(raw));e["matrix"]["xml_verified"]=True
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):contract.validate_evidence(e,SHA,QA,"123-1")

    def test_matrix_rejects_stale_identity_inconsistent_counters_exits_and_teardown(self):
        for mutation in ("sha","request","run","count","exit","timeout","parser","cleanup","encryption","full","mode"):
            raw=matrix_fixture()
            if mutation=="sha":raw["source_sha"]=QA
            if mutation=="request":raw["request_id"]="124-1"
            if mutation=="run":raw["run_id"]="not-a-run"
            if mutation=="count":raw["lane_results"][1]["tests"]=342
            if mutation=="exit":raw["lane_results"][1]["exit_code"]=1
            if mutation=="timeout":raw["lane_results"][1]["timed_out"]=True
            if mutation=="parser":raw["lane_results"][1]["parser_issues"]=["PRIVATE_LOG"]
            if mutation=="cleanup":raw["cleanup_status"]="NOT_PASS"
            if mutation=="encryption":raw["encrypted_recovery"]="NOT_IMPLEMENTED_IN_EXISTING_TEST"
            if mutation=="full":raw["full_verification"]="NOT_PASS"
            if mutation=="mode":raw["mode"]="Ordinary"
            e=evidence();e.update(schema_version=2,matrix=public_matrix(raw));e["matrix"]["xml_verified"]=True
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):contract.validate_evidence(e,SHA,QA,"123-1")
            self.assertNotIn("PRIVATE_LOG",json.dumps(e))

    def test_hashed_array_digest_and_trusted_inventory_pin_are_required(self):
        for key in ("inventory","method_results","lane_results"):
            e=schema2_evidence();e["matrix"][key].reverse()
            with self.subTest(key=key),self.assertRaises(ValueError):contract.validate_evidence(e,SHA,QA,"123-1")
        e=schema2_evidence()
        with self.assertRaises(ValueError):contract.validate_evidence(e,SHA,QA,"123-1",expected_inventory_sha256="0"*64)

    def test_schema1_cannot_be_used_for_new_report(self):
        import inspect
        self.assertIn("required_schema",inspect.signature(contract.validate_evidence).parameters)
        with self.assertRaises(ValueError):contract.validate_evidence(evidence(),SHA,QA,"123-1",required_schema=2)

    def test_schema2_summary_counts_and_empty_teardown_cannot_claim_complete(self):
        for mutation in ("summary","resources","cleanup"):
            e=schema2_evidence()
            if mutation=="summary":e["full_maven"]["tests"]=351
            else:
                e["matrix"]["teardown"]["resource_observations" if mutation=="resources" else "cleanup_observations"]=[]
                e["matrix"]["teardown"]["sha256"]=digest({k:e["matrix"]["teardown"][k] for k in
                    ("resource_observations","cleanup_observations")})
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):contract.validate_evidence(e,SHA,QA,"123-1")

    def test_resource_image_identity_is_observed_and_required(self):
        raw=matrix_fixture();normalized=public_matrix(raw)
        self.assertEqual(normalized["teardown"]["resource_observations"][0].get("image_id"),"sha256:"+"f"*64)
        for value in (None,"postgres:17-alpine","sha256:not-a-digest"):
            raw=matrix_fixture();raw["resource_observations"][0]["image_id"]=value
            e=schema2_evidence();e["matrix"]=public_matrix(raw);e["matrix"]["xml_verified"]=True
            with self.subTest(value=value),self.assertRaises(ValueError):contract.validate_evidence(e,SHA,QA,"123-1")

    def test_resource_purpose_loopback_and_database_marker_bind_to_required_pairs(self):
        for mutation in ("purpose","loopback","marker"):
            raw=matrix_fixture()
            if mutation=="purpose":raw["resource_observations"][0]["purpose"]="unrelated"
            if mutation=="loopback":raw["resource_observations"][0]["loopback"]=False
            e=schema2_evidence();e["matrix"]=public_matrix(raw);e["matrix"]["xml_verified"]=True
            if mutation=="marker":e["database_run_id"]="44444444-4444-4444-8444-444444444444"
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):contract.validate_evidence(e,SHA,QA,"123-1")

    def test_independent_xml_checks_ids_counters_and_source_run_binding(self):
        self.assertTrue(hasattr(collector,"verify_matrix_xml"),"independent matrix XML verification is required")
        for mutation in ("good","duplicate","missing","unexpected","counters","skip","sha","run","lane","dtd","malformed"):
            with tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);raw=matrix_fixture();groups=[]
                for lane in LANES:
                    rows=[r for r in raw["method_results"] if r["lane"]==lane]
                    cases=''.join('<testcase classname="'+r["id"].split("#")[0]+'" name="'+r["id"].split("#")[1]+'"/>' for r in rows)
                    props=''.join('<property name="'+k+'" value="'+v+'"/>' for k,v in
                                  (("win11p.run.id",MATRIX_RUN),("win11p.source.sha",SHA),("win11p.lane",lane)))
                    xml='<testsuite tests="'+str(len(rows))+'" failures="0" errors="0" skipped="0"><properties>'+props+'</properties>'+cases+'</testsuite>'
                    if lane=="discovery":
                        if mutation=="duplicate":xml=xml.replace('</testsuite>',cases+'</testsuite>')
                        if mutation=="missing":xml=xml.replace(cases,"")
                        if mutation=="unexpected":xml=xml.replace('name="discovery"','name="unexpected"')
                        if mutation=="counters":xml=xml.replace('tests="1"','tests="2"')
                        if mutation=="skip":xml=xml.replace('/></testsuite>','><skipped/></testcase></testsuite>')
                        if mutation=="sha":xml=xml.replace(SHA,QA)
                        if mutation=="run":xml=xml.replace(MATRIX_RUN,"f"*32)
                        if mutation=="lane":xml=xml.replace('value="discovery"','value="ordinary"')
                        if mutation=="dtd":xml='<!DOCTYPE x>'+xml
                        if mutation=="malformed":xml='<testsuite'
                    path=root/(lane+'.xml');path.write_text(xml)
                    groups.append(dict(lane=lane,paths=[str(path)]))
                if mutation=="good":collector.verify_matrix_xml(raw,groups,SHA,"123-1")
                else:
                    with self.subTest(mutation=mutation),self.assertRaises(ValueError):collector.verify_matrix_xml(raw,groups,SHA,"123-1")

if __name__=="__main__":unittest.main()
