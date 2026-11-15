import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import win11p_control as control
from test_win11p_contract import evidence,SHA,QA,DIGEST

class ControlTests(unittest.TestCase):
    def fixture(self):
        e=evidence();encoded=json.dumps(e).encode()
        out=io.BytesIO()
        with zipfile.ZipFile(out,"w") as z:z.writestr("evidence.json",encoded)
        raw=out.getvalue()
        meta=dict(id=12,name="win11p-evidence-123-1",expired=False,
            digest="sha256:"+hashlib.sha256(raw).hexdigest(),workflow_run=dict(id=123,head_sha=QA))
        c=dict(source_sha=SHA,qa_sha=QA,run_id="123",run_attempt="1",
               operator="operator",reviewer="reviewer")
        receipt={k:e[k] for k in ("plan_id","source_sha","qa_sha","request_id","run_id","run_attempt")}
        receipt.update(artifact_id=12,evidence_sha256=hashlib.sha256(encoded).hexdigest(),
                       disposition="PASS",operator_workflow_confirmed=True)
        comments=[dict(user=dict(login=login,type="User"),body=json.dumps(receipt))
                  for login in ("operator","reviewer")]
        return e,raw,meta,c,comments

    def run_report(self,raw,meta,c,comments,result="success"):
        args=types.SimpleNamespace(artifact_id="12",source_bundle_sha=DIGEST,qa_archive_sha=DIGEST)
        def api(path):
            return raw if path.endswith("/zip") else json.dumps(meta).encode()
        with patch.object(control,"checked_context",return_value=({},c,dict(user=dict(login="author")),dict(user=dict(login="qa-author")))),\
             patch.object(control,"gh",side_effect=api),\
             patch.object(control.subprocess,"check_output",return_value=json.dumps([comments]).encode()),\
             patch.dict(os.environ,{"GITHUB_REPOSITORY":"ARG-Digital-Solutions/aronexa-qa-central","EXECUTION_RESULT":result}):
            with contextlib.redirect_stdout(io.StringIO()):control.report(args)

    def test_mocked_report_prepares_payload_only_after_both_independent_receipts(self):
        e,raw,meta,c,comments=self.fixture()
        with tempfile.TemporaryDirectory() as tmp:
            old=os.getcwd()
            try:
                os.chdir(tmp);self.run_report(raw,meta,c,comments)
                result=json.loads(Path("status.json").read_text())
                self.assertEqual(result["context"],"aronexa/central-qa/WIN11P_RECEPTION_E2E")
                self.assertEqual(result["description"],"request=123-1; qa=success; release-not-authorized")
            finally:os.chdir(old)

    def test_missing_operator_receipt_or_failed_job_writes_no_status(self):
        for result,drop in [("failure",False),("success",True)]:
            e,raw,meta,c,comments=self.fixture()
            if drop:comments=comments[1:]
            with tempfile.TemporaryDirectory() as tmp:
                old=os.getcwd()
                try:
                    os.chdir(tmp)
                    with self.assertRaises(ValueError):self.run_report(raw,meta,c,comments,result)
                    self.assertFalse(Path("status.json").exists())
                finally:os.chdir(old)

    def test_latest_negative_reviewer_receipt_cannot_reuse_earlier_pass(self):
        e,raw,meta,c,comments=self.fixture()
        bad=json.loads(comments[-1]["body"]);bad["disposition"]="FAIL"
        comments.append(dict(user=dict(login="reviewer",type="User"),body=json.dumps(bad)))
        with tempfile.TemporaryDirectory() as tmp:
            old=os.getcwd()
            try:
                os.chdir(tmp)
                with self.assertRaises(ValueError):self.run_report(raw,meta,c,comments)
                self.assertFalse(Path("status.json").exists())
            finally:os.chdir(old)

    def test_control_rejects_other_qa_repository_before_reading_data(self):
        with patch.dict(os.environ,{"GITHUB_REPOSITORY":"attacker/fork"}),patch.object(control,"load") as load:
            with self.assertRaises(ValueError):control.checked_context()
            load.assert_not_called()

if __name__=="__main__":unittest.main()
