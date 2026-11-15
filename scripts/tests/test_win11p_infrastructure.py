import hashlib
from pathlib import Path
import re
import unittest

ROOT=Path(__file__).resolve().parents[2]
class InfrastructureTests(unittest.TestCase):
    def test_legacy_controller_and_workflow_are_byte_identical(self):
        pins={".github/workflows/qa-cross-repo-handoff.yml":"271c9f82e582b3b63536f5259109314735182976",
              ".github/workflows/qa-int-reg01.yml":"32f14644dd5966318841d47bb7a8bb81534bd2ec"}
        for name,digest in pins.items():
            # Git checkouts may convert LF to CRLF; compare canonical text bytes.
            raw=(ROOT/name).read_bytes().replace(b"\r\n",b"\n")
            expected=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
            self.assertEqual(expected,digest)

    def test_new_workflow_is_manual_and_default_denied(self):
        s=(ROOT/".github/workflows/qa-win11p-reception.yml").read_text()
        event=s.split("on:\n",1)[1].split("permissions:",1)[0]
        self.assertIn("workflow_dispatch:",event)
        self.assertNotIn("pull_request",event)
        self.assertNotIn("repository_dispatch",event)
        self.assertIn('test "$GITHUB_REF" = refs/heads/main',s)
        self.assertIn('test "$GITHUB_SHA" = "$AUTHORIZED_QA_SHA"',s)
        self.assertIn('test "$WINDOWS_RUNNER_APPROVED" = true',s)

    def test_execution_has_no_source_or_status_credential(self):
        s=(ROOT/".github/workflows/qa-win11p-reception.yml").read_text()
        execution=s.split("\n  execute:",1)[1].split("\n  report:",1)[0]
        self.assertNotIn("secrets.",execution)
        self.assertNotIn("GH_TOKEN",execution)
        self.assertNotIn("actions/checkout",execution)
        self.assertNotIn("statuses:",execution)
        self.assertIn("win11p-public/evidence.json",execution)

    def test_reporter_never_checks_out_or_executes_product_source(self):
        s=(ROOT/".github/workflows/qa-win11p-reception.yml").read_text().split("\n  report:",1)[1]
        self.assertNotIn("npm",s);self.assertNotIn("mvn",s)
        self.assertNotIn("repository: ARG-Digital-Solutions/aronexa-healthcare-platform",s)
        self.assertIn("win11p_control.py report",s)
        self.assertIn("ARONEXA_DEV_STATUS_TOKEN",s)

    def test_windows_runner_enrollment_denial_precedes_any_port_or_docker_use(self):
        s=(ROOT/"scripts/Invoke-Win11pReception.ps1").read_text()
        self.assertLess(s.index("runner not enrolled"),s.index("TcpListener"))
        self.assertLess(s.index("refuses inherited credentials"),s.index("TcpListener"))
        self.assertIn("ALL-MODULE-PATH",s)
        self.assertIn("-PreviewPort 5186",s)
        self.assertNotIn("PackageOnlyUnverified",s)

    def test_plan_keeps_legacy_and_manual_contracts_separate(self):
        s=(ROOT/"scripts/check_qa_plans.py").read_text()
        self.assertIn('if plan_id == "WIN11P_RECEPTION_E2E":',s)
        self.assertIn('valid_workflows = {"qa-int-reg01.yml"}',s)
        self.assertIn('required_checks = {"maven_verify_and_testcontainers", "verified_playwright"}',s)

if __name__=="__main__":unittest.main()
