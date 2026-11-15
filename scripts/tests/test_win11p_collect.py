import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from win11p_collect import collect,totals,runtime_hash,postgres_observed
from win11p_contract import validate_evidence,GATES
SHA="a"*40
QA="b"*40
RUN="11111111-1111-4111-8111-111111111111"
OP="22222222-2222-4222-8222-222222222222"

class CollectorTests(unittest.TestCase):
    def fixture(self,root):
        def put(name,value):
            p=root/name;p.write_text(value,encoding="utf-8");return str(p)
        runtime=root/"runtime";runtime.mkdir();(runtime/"release").write_text('JAVA_VERSION="21.0.13"')
        def xml(name,n,method="case"):
            props='<properties><property name="java.version" value="21.0.13"/><property name="password" value="DO_NOT_PUBLISH"/><property name="java.home" value="'+runtime.as_posix()+'"/></properties>'
            return put(name,'<testsuite tests="'+str(n)+'" failures="0" errors="0" skipped="0">'+props+
                ''.join('<testcase name="'+(method if n==1 else method+str(i))+'"/>' for i in range(n))+'</testsuite>')
        records=[dict(run_id=r,version_num=170011,container_id="c"*64,
            database_name="aronexa_pilot05_disposable_only",loopback=True) for r in (RUN,OP)]
        summary="SourceCommit="+SHA+"\nRunId="+RUN+"\nRc03PreviewPort=5186\n"
        summary+="".join(k+"=true\n" for k in ("Rc03BrowserCreatedRegistration","Rc03BrowserCreatedBookingAndCheckIn",
            "Rc03DuplicateRegistrationDenied","Rc03SameMarkedPG17RecoveredDifferentJvm"))
        d=dict(context=dict(source_sha=SHA,qa_sha=QA,request_id="123-1",run_id="123",run_attempt="1",
            source_bundle_sha256="d"*64,qa_archive_sha256="e"*64),
            source_clean=True,versions=dict(java=21,node=24,postgres=17),
            frontend_log=put("front.log","# tests 249\n# pass 249\n# fail 0\n# cancelled 0\n# skipped 0\n"),
            frontend_exit=0,build_exit=0,search_xml=xml("search.xml",7),roles_xml=xml("roles.xml",4),
            rls_xml=xml("rls.xml",8),full_maven_reports=[xml("full.xml",2)],full_maven_exit=0,
            phase_a_xml=xml("a.xml",1,"phaseARc03BrowserCreatesRegistrationBookingAndCheckIn"),
            phase_b_xml=xml("b.xml",1,"phaseBRc03RecoversBrowserCreatedPatientAndCheckedInQueue"),
            rc03_exit=0,rc03_summary=put("summary.txt",summary),
            rc03_log=put("rc03.log","DO_NOT_PUBLISH password\nPILOT08_RC03_PHASE_A_PID=101\nPILOT08_RC03_PHASE_B_PID=202\n"),
            runtime_home=str(runtime),runtime_sha256=runtime_hash(runtime),
            postgres_observations=put("postgres.jsonl","\n".join(json.dumps(r) for r in records)),
            operator_observation=put("operator.txt","PatientRecordsCreated=1\nCheckedInAppointments=1\n"),
            operator_summary=put("operator-summary.txt","SourceCommit="+SHA+"\nRunId="+OP+"\n"),
            operator_exit=0,operator_xml=xml("op.xml",1,"pilot09OperatorAssistedWindowsFictionalLab"))
        return d

    def execute(self,root,d):
        p=root/"private.json";p.write_text(json.dumps(d));return collect(p)

    def test_complete_sanitized_evidence_and_no_raw_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);d=self.fixture(root);e=self.execute(root,d)
            validate_evidence(e,SHA,QA,"123-1")
            public=json.dumps(e)
            self.assertNotIn("DO_NOT_PUBLISH",public)
            self.assertNotIn(tmp,public)
            self.assertEqual(e["roles"]["tests"],4)
            self.assertEqual(e["rls"]["tests"],8)

    def test_missing_phase_report_blocks_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);d=self.fixture(root);d["phase_b_xml"]=str(root/"absent")
            e=self.execute(root,d);self.assertEqual(e["gates"][GATES[5]],"FAIL")
            with self.assertRaises(ValueError):validate_evidence(e,SHA,QA,"123-1")

    def test_portable_jvm_cannot_fall_back_or_mutate(self):
        for kind in ("home","mutation","version"):
            with tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);d=self.fixture(root)
                if kind=="home":d["runtime_home"]=str(root/"other")
                elif kind=="mutation":(root/"runtime/release").write_text("CHANGED")
                else:
                    path=Path(d["phase_b_xml"]);path.write_text(path.read_text().replace("21.0.13","22.0.1"))
                e=self.execute(root,d);self.assertEqual(e["gates"][GATES[1]],"FAIL")

    def test_zero_operator_observation_never_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);d=self.fixture(root)
            Path(d["operator_observation"]).write_text("PatientRecordsCreated=0\nCheckedInAppointments=0\n")
            self.assertEqual(self.execute(root,d)["gates"][GATES[6]],"FAIL")

    def test_full_maven_hidden_failed_skipped_or_missing_cases_rejected(self):
        for child in ("<testcase><skipped/></testcase>","<testcase><failure/></testcase>",
                      "<testcase><error/></testcase>",""):
            with tempfile.TemporaryDirectory() as tmp:
                p=Path(tmp)/"full.xml"
                p.write_text('<testsuite tests="1" failures="0" errors="0" skipped="0">'+child+'</testsuite>')
                with self.assertRaises(ValueError):totals([p])

    def test_full_maven_failures_are_preserved_and_block_positive_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);d=self.fixture(root);d["full_maven_exit"]=1
            Path(d["full_maven_reports"][0]).write_text(
                '<testsuite tests="1" failures="1" errors="0" skipped="0"><testcase><failure>PRIVATE</failure></testcase></testsuite>')
            e=self.execute(root,d)
            self.assertEqual(e["full_maven"]["failures"],1)
            self.assertEqual(e["gates"][GATES[7]],"FAIL")

    def test_wrong_pg_major_or_run_marker_is_rejected(self):
        for field,value in [("version_num",180000),("loopback",False),("run_id",OP)]:
            with tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);d=self.fixture(root)
                r=dict(run_id=RUN,version_num=170011,container_id="c"*64,
                       database_name="aronexa_pilot05_disposable_only",loopback=True)
                r[field]=value;Path(d["postgres_observations"]).write_text(json.dumps(r))
                with self.assertRaises(ValueError):postgres_observed(d["postgres_observations"],RUN)

    def test_skipped_frontend_blocks_even_if_exit_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);d=self.fixture(root)
            Path(d["frontend_log"]).write_text("# tests 249\n# pass 249\n# fail 0\n# cancelled 0\n# skipped 1\n")
            self.assertEqual(self.execute(root,d)["gates"][GATES[2]],"FAIL")

if __name__=="__main__":unittest.main()
