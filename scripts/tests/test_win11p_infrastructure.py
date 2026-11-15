import hashlib
import copy
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
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
        self.assertNotIn("PackageOnlyUnverified",s)

    def test_executor_runs_matrix_once_after_portable_runtime_creation(self):
        s=(ROOT/"scripts/Invoke-Win11pReception.ps1").read_text()
        self.assertEqual(s.count("Invoke-Win11p-MavenMatrix.ps1"),1)
        self.assertNotRegex(s,r"&\s+mvn\.cmd")
        self.assertNotIn("Test-AroNexa-Pilot05-DistinctJvm-Restart.ps1",s)
        self.assertNotIn("Start-AroNexa-WindowsAssistedPilot.ps1",s)
        self.assertLess(s.index("--add-modules ALL-MODULE-PATH"),s.index("Invoke-Win11p-MavenMatrix.ps1"))
        self.assertIn("WIN11P_PORTABLE_JAVA_HOME",s)
        self.assertNotIn("$env:MAVEN_OPTS=",s)

    def test_executor_preserves_protected_authorization_provenance_and_private_inputs(self):
        s=(ROOT/"scripts/Invoke-Win11pReception.ps1").read_text()
        for key in ("WIN11P_EXECUTION_AUTHORIZATION_JSON","WIN11P_EXECUTION_AUTHORIZATION_SHA256",
                    "WIN11P_AUTHORIZATION_VERIFIED_SHA256","WIN11P_AUTHORIZATION_REQUEST_ID"):
            self.assertIn(key,s)
        self.assertIn("$authorization.qa_sha -ne $c.qa_sha",s)
        self.assertIn("$authorization.source_sha -ne $c.source_sha",s)
        self.assertIn("$authorization.request_id -ne $c.request_id",s)
        self.assertNotIn("ConfirmFictionalDisposableLab",s)
        self.assertNotRegex(s,r"\$env:ARONEXA_[A-Z0-9_]*ACK\s*=")

    def test_executor_passes_actual_lane_reports_and_collects_from_finally(self):
        s=(ROOT/"scripts/Invoke-Win11pReception.ps1").read_text()
        for key in ("matrix_results_path","matrix_execution_run_id","matrix_report_paths","rc03_logs"):
            self.assertIn(key,s)
        self.assertIn("SESSION-OBSERVATION.txt",s)
        self.assertIn("win11p-reports",s)
        self.assertIn("ordinary",s)
        self.assertIn("finally",s.split("matrix_results_path",1)[1])
        self.assertIn("win11p_collect.py",s[s.rindex("finally"):])

    def test_workflow_uses_protected_authorization_values_without_public_upload(self):
        s=(ROOT/".github/workflows/qa-win11p-reception.yml").read_text()
        execution=s.split("\n  execute:",1)[1].split("\n  report:",1)[0]
        for key in ("WIN11P_EXECUTION_AUTHORIZATION_JSON","WIN11P_EXECUTION_AUTHORIZATION_SHA256",
                    "WIN11P_AUTHORIZATION_VERIFIED_SHA256","WIN11P_AUTHORIZATION_REQUEST_ID"):
            self.assertIn("${{ vars."+key+" }}",execution)
        self.assertIn("win11p-public/evidence.json",execution)
        self.assertNotIn("authorization.json\n",execution)

    def test_observer_limits_matrix_containers_to_current_source_and_request(self):
        s=(ROOT/"scripts/Observe-Win11pPostgres.ps1").read_text()
        for key in ("com.argdigital.aronexa.win11p.request","com.argdigital.aronexa.win11p.source","com.argdigital.aronexa.win11p.purpose"):
            self.assertIn(key,s)
        self.assertIn("$RequestId",s)
        self.assertIn("$SourceSha",s)
        self.assertIn("aronexa-win11p-",s)
        self.assertIn("$item.Config.Image -ne 'postgres:17-alpine'",s)

    @unittest.skipUnless(shutil.which("pwsh"),"PowerShell runtime unavailable")
    def test_postgres_observer_accepts_only_current_owned_pg17_loopback_identity(self):
        run="11111111-1111-4111-8111-111111111111"
        labels={"com.argdigital.aronexa.pilot05.run":run,
                "com.argdigital.aronexa.win11p.request":"123-1",
                "com.argdigital.aronexa.win11p.source":"a"*40,
                "com.argdigital.aronexa.win11p.purpose":"rc03"}
        valid={"Id":"b"*64,"Image":"sha256:"+"c"*64,"Name":"/aronexa-win11p-rc03-"+run.replace("-",""),
               "Config":{"Image":"postgres:17-alpine","Labels":labels},
               "NetworkSettings":{"Ports":{"5432/tcp":[{"HostIp":"127.0.0.1","HostPort":"49152"}]}}}
        cases=[("valid",valid,"170004",True),
               ("postgres16",valid,"160004",False),
               ("malformed_version",valid,"17.4",False)]
        for label,value in (("com.argdigital.aronexa.win11p.request","999-1"),
                            ("com.argdigital.aronexa.win11p.source","c"*40),
                            ("com.argdigital.aronexa.win11p.purpose","unowned"),
                            ("com.argdigital.aronexa.pilot05.run","invalid")):
            fixture=copy.deepcopy(valid);fixture["Config"]["Labels"][label]=value
            cases.append((label,fixture,"170004",False))
        for key,value in (("Name","/unowned"),("Id","b"*12),("Image","postgres:17-alpine")):
            fixture=copy.deepcopy(valid);fixture[key]=value;cases.append((key,fixture,"170004",False))
        fixture=copy.deepcopy(valid);fixture["Config"]["Image"]="postgres:latest"
        cases.append(("image",fixture,"170004",False))
        for key,value in (("HostIp","0.0.0.0"),("HostPort","5433"),("HostPort","99999")):
            fixture=copy.deepcopy(valid);fixture["NetworkSettings"]["Ports"]["5432/tcp"][0][key]=value
            cases.append((key+value,fixture,"170004",False))
        for name,fixture,version,expected in cases:
            with self.subTest(name=name),tempfile.TemporaryDirectory() as temp:
                root=Path(temp);stop=root/"stop";evidence=root/"observations.jsonl"
                inspect=root/"inspect.json";inspect.write_text(json.dumps([fixture]))
                fake=root/"fake-docker.py"
                fake.write_text("#!"+sys.executable+"\nimport os,sys\nfrom pathlib import Path\n"
                    "if sys.argv[1]=='ps':\n Path(os.environ['WIN11P_TEST_STOP']).write_text('STOP')\n print('b'*12)\n"
                    "elif sys.argv[1]=='inspect':\n print(Path(os.environ['WIN11P_TEST_INSPECT']).read_text())\n"
                    "elif sys.argv[1]=='exec':\n print(os.environ['WIN11P_TEST_VERSION'])\n")
                docker=fake
                if os.name=="nt":
                    docker=root/"fake-docker.cmd"
                    docker.write_text('@"'+sys.executable+'" "'+str(fake)+'" %*\r\n')
                else:fake.chmod(0o700)
                env={**os.environ,"WIN11P_TEST_STOP":str(stop),"WIN11P_TEST_INSPECT":str(inspect),"WIN11P_TEST_VERSION":version}
                result=subprocess.run(["pwsh","-NoProfile","-NonInteractive","-File",str(ROOT/"scripts/Observe-Win11pPostgres.ps1"),
                    "-EvidencePath",str(evidence),"-StopFile",str(stop),"-DockerPath",str(docker),"-RequestId","123-1","-SourceSha","a"*40],
                    env=env,capture_output=True,text=True,timeout=15)
                self.assertEqual(result.returncode,0,result.stderr)
                self.assertEqual(evidence.exists(),expected)
                if expected:
                    record=json.loads(evidence.read_text().strip())
                    self.assertEqual(record,{"run_id":run,"version_num":170004,"container_id":"b"*64,"image_id":"sha256:"+"c"*64,
                        "database_name":"aronexa_pilot05_disposable_only","loopback":True})

    @unittest.skipUnless(shutil.which("pwsh"),"PowerShell runtime unavailable")
    def test_authorization_function_rejects_unbound_or_self_declared_inputs(self):
        context={"source_sha":"a"*40,"qa_sha":"b"*40,"request_id":"123-1","plan_id":"WIN11P_RECEPTION_E2E",
                 "reviewer":"independent-reviewer","operator":"independent-operator"}
        authorization={**{key:context[key] for key in ("source_sha","qa_sha","request_id","plan_id","reviewer")},
            "review_url":"https://github.com/ARG-Digital-Solutions/aronexa-qa-central/issues/38#issuecomment-123",
            "disposition":"APPROVED_FOR_EXECUTION","lanes":[]}
        cases=[("bound",authorization,{},True)]
        for key,value in (("source_sha","c"*40),("qa_sha","d"*40),("request_id","999-1"),
                          ("reviewer","implementation-author"),("review_url","https://example.com/review"),
                          ("credentials","must-never-be-an-authorization-field")):
            candidate=copy.deepcopy(authorization);candidate[key]=value;cases.append((key,candidate,{},False))
        candidate=copy.deepcopy(authorization);candidate["lanes"]=[{"id":"pilot09-operator","operator":"implementation-author"}]
        cases.append(("unreviewed-lane-operator",candidate,{},False))
        cases.append(("stale-operator-lab",authorization,{},False))
        candidate=copy.deepcopy(authorization);candidate["lanes"]=[{"id":"pilot09-operator","operator":context["operator"],
            "environment":{"ARONEXA_PILOT09_RUN_DIR":"reviewed-run-placeholder"}}]
        for name,expected in (("reviewed-operator-lab",True),("reviewed-operator-lab-wrongmarker",False),("extra-operator-lab",False)):
            cases.append((name,candidate,{},expected))
        for key,value in (("WIN11P_EXECUTION_AUTHORIZATION_JSON",""),("WIN11P_EXECUTION_AUTHORIZATION_SHA256","0"*64),
                          ("WIN11P_AUTHORIZATION_VERIFIED_SHA256","0"*64),("WIN11P_AUTHORIZATION_REQUEST_ID","999-1")):
            cases.append((key,authorization,{key:value},False))
        for name,candidate,overrides,expected in cases:
            with self.subTest(name=name),tempfile.TemporaryDirectory() as temp:
                candidate=copy.deepcopy(candidate)
                if name in ("stale-operator-lab","reviewed-operator-lab","reviewed-operator-lab-wrongmarker","extra-operator-lab"):
                    labs=Path(temp)/"ARG-Digital"/"AroNexa-Pilot09-Disposable"
                    run=labs/("pilot09-"+"1"*32);run.mkdir(parents=True)
                    (run/"LAB-TEST-ONLY.marker").write_text("FICTIONAL_DISPOSABLE_ONLY_SOURCE_SHA="+("c"*40 if "wrongmarker" in name else context["source_sha"]))
                    if name!="stale-operator-lab":candidate["lanes"][0]["environment"]["ARONEXA_PILOT09_RUN_DIR"]=str(run)
                    if name=="extra-operator-lab":(labs/("pilot09-"+"2"*32)).mkdir()
                raw=json.dumps(candidate);digest=hashlib.sha256(raw.encode()).hexdigest()
                env={**os.environ,"LOCALAPPDATA":temp,"WIN11P_EXECUTION_AUTHORIZATION_JSON":raw,
                     "WIN11P_EXECUTION_AUTHORIZATION_SHA256":digest,"WIN11P_AUTHORIZATION_VERIFIED_SHA256":digest,
                     "WIN11P_AUTHORIZATION_REQUEST_ID":"123-1",**overrides}
                driver=Path(temp)/"authorization-test.ps1"
                driver.write_text("Set-StrictMode -Version Latest\n$ErrorActionPreference='Stop'\n"
                    "$errors=$null;$ast=[System.Management.Automation.Language.Parser]::ParseFile($args[0],[ref]$null,[ref]$errors)\n"
                    "foreach($name in @('Assert-Hash','Read-ExecutionAuthorization')){\n"
                    " $node=$ast.Find({param($n)$n -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq $name},$true)\n"
                    " . ([scriptblock]::Create($node.Extent.Text))\n}\n"
                    "$c=ConvertFrom-Json $args[2];$work=$args[1]\ntry{\n"
                    " $path=Read-ExecutionAuthorization\n if(-not(Test-Path -LiteralPath $path)){exit 2}\n"
                    " if($env:WIN11P_EXECUTION_AUTHORIZATION_JSON){exit 3}\n exit 0\n}catch{exit 1}\n")
                result=subprocess.run(["pwsh","-NoProfile","-NonInteractive","-File",str(driver),
                    str(ROOT/"scripts/Invoke-Win11pReception.ps1"),temp,json.dumps(context)],env=env,capture_output=True,text=True,timeout=15)
                self.assertEqual(result.returncode==0,expected,result.stderr)

    @unittest.skipUnless(shutil.which("pwsh"),"PowerShell runtime unavailable")
    def test_powershell_scripts_parse_and_executor_denies_non_windows(self):
        for name in ("Invoke-Win11pReception.ps1","Observe-Win11pPostgres.ps1"):
            path=str(ROOT/"scripts"/name).replace("'","''")
            result=subprocess.run(["pwsh","-NoProfile","-NonInteractive","-Command",
                "$errors=$null;[void][System.Management.Automation.Language.Parser]::ParseFile('"+path+"',[ref]$null,[ref]$errors);if($errors.Count){exit 1}"],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
        if os.name!="nt":
            with tempfile.TemporaryDirectory() as temp:
                result=subprocess.run(["pwsh","-NoProfile","-NonInteractive","-File",str(ROOT/"scripts/Invoke-Win11pReception.ps1"),
                    "-InputDirectory",temp,"-ExpectedContextSha","a"*64,"-ExpectedSourceBundleSha","b"*64,"-ExpectedQaArchiveSha","c"*64],capture_output=True,text=True)
                self.assertNotEqual(result.returncode,0)
                self.assertIn("WIN11P requires Windows",result.stderr)

    def test_plan_keeps_legacy_and_manual_contracts_separate(self):
        s=(ROOT/"scripts/check_qa_plans.py").read_text()
        self.assertIn('if plan_id == "WIN11P_RECEPTION_E2E":',s)
        self.assertIn('valid_workflows = {"qa-int-reg01.yml"}',s)
        self.assertIn('required_checks = {"maven_verify_and_testcontainers", "verified_playwright"}',s)

if __name__=="__main__":unittest.main()
