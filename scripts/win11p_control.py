"""Trusted QA control-plane I/O. Never imports or executes application Python."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from win11p_contract import (
    PLAN,GATES,REPOSITORY,require,validate_plan,validate_context,validate_scope,
    validate_evidence,validate_receipt,validate_artifact_metadata,read_artifact,
)

ROOT=Path(__file__).resolve().parents[1]

def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))

def git(path,*args):
    return subprocess.check_output(["git","-C",str(path),*args],stderr=subprocess.DEVNULL).decode().strip()

def context():
    return dict(event=os.environ.get("GITHUB_EVENT_NAME"),ref=os.environ.get("GITHUB_REF"),
        qa_sha=os.environ.get("GITHUB_SHA"),authorized_qa_sha=os.environ.get("AUTHORIZED_QA_SHA"),
        source_sha=os.environ.get("SOURCE_SHA"),acknowledgement=os.environ.get("DISPOSABLE_ACK")=="true",
        runner_approved=os.environ.get("WINDOWS_RUNNER_APPROVED")=="true",
        reviewer=os.environ.get("REVIEWER_LOGIN"),operator=os.environ.get("OPERATOR_LOGIN"),
        reviewed_qa_sha=os.environ.get("REVIEWED_QA_SHA"),run_id=os.environ.get("GITHUB_RUN_ID"),
        run_attempt=os.environ.get("GITHUB_RUN_ATTEMPT"))

def checked_context():
    require(os.environ.get("GITHUB_REPOSITORY")=="ARG-Digital-Solutions/aronexa-qa-central","wrong QA repository")
    plan=load(ROOT/"qa/plans/WIN11P_RECEPTION_E2E.json")
    validate_plan(plan,ROOT)
    c=context()
    pr=load("source-pr.json");qa=load("qa-pr.json");reviews=load("qa-reviews.json")
    if reviews and isinstance(reviews[0],list):reviews=[r for page in reviews for r in page]
    validate_context(plan,pr,qa,reviews,c)
    # Approval of a different/squashed QA commit is valid only for identical execution inputs.
    delta=git(ROOT,"diff","--name-only",c["reviewed_qa_sha"],c["qa_sha"],"--",
        "scripts",".github/workflows","qa/plans","package.json","package-lock.json")
    require(not delta,"execution inputs differ from independently reviewed QA revision")
    return plan,c,pr,qa

def file_hash(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b""):h.update(chunk)
    return h.hexdigest()

def prepare(args):
    plan,c,pr,qa=checked_context()
    app=Path(args.app)
    require(git(app,"rev-parse","HEAD")==c["source_sha"],"checkout SHA mismatch")
    require(not git(app,"status","--porcelain","--untracked-files=no"),"tracked source dirty")
    subprocess.run(["git","-C",str(app),"merge-base","--is-ancestor",
                    plan["source_baseline_sha"],c["source_sha"]],check=True,
                    stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    validate_scope(plan,git(app,"diff","--name-only",plan["source_baseline_sha"],c["source_sha"]).splitlines())
    target=Path(args.output);target.mkdir(parents=True,exist_ok=False)
    subprocess.run(["git","-C",str(app),"bundle","create",str(target/"source.bundle"),"HEAD"],
                   check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    subprocess.run(["git","-C",str(ROOT),"archive","--format=zip",
                    "--output="+str(target/"qa.zip"),c["qa_sha"]],check=True)
    record={**c,"plan_id":PLAN,"request_id":c["run_id"]+"-"+c["run_attempt"],
            "source_bundle_sha256":file_hash(target/"source.bundle"),
            "qa_archive_sha256":file_hash(target/"qa.zip"),
            "app_author":pr["user"]["login"],"qa_author":qa["user"]["login"]}
    (target/"context.json").write_text(json.dumps(record,sort_keys=True)+"\n",encoding="utf-8")
    outputs={k:record[k] for k in ("source_bundle_sha256","qa_archive_sha256")}
    outputs["context_sha256"]=file_hash(target/"context.json")
    with open(os.environ["GITHUB_OUTPUT"],"a",encoding="utf-8") as stream:
        for k,v in outputs.items():stream.write(k+"="+v+"\n")
    print("WIN11P exact-source inputs prepared; execution not yet approved as PASS")

def gh(path):
    # Reporter only: token is QA-repository read scope here, never product status scope.
    return subprocess.check_output(["gh","api",path],stderr=subprocess.DEVNULL)

def report(args):
    plan,c,pr,qa=checked_context() # Recheck live PR and admin pin after execution.
    require(os.environ.get("EXECUTION_RESULT")=="success","execution job did not succeed")
    artifact_id=int(args.artifact_id)
    metadata=json.loads(gh("repos/"+os.environ["GITHUB_REPOSITORY"]+"/actions/artifacts/"+str(artifact_id)))
    digest=metadata.get("digest","").removeprefix("sha256:")
    validate_artifact_metadata(metadata,c["run_id"],c["run_attempt"],c["qa_sha"],artifact_id,digest)
    raw=gh("repos/"+os.environ["GITHUB_REPOSITORY"]+"/actions/artifacts/"+str(artifact_id)+"/zip")
    data=read_artifact(raw,digest)
    request=c["run_id"]+"-"+c["run_attempt"]
    validate_evidence(data,c["source_sha"],c["qa_sha"],request)
    expected={"source_bundle_sha256":args.source_bundle_sha,"qa_archive_sha256":args.qa_archive_sha}
    require(all(data[k]==v for k,v in expected.items()),"evidence/input bundle mismatch")
    # Hash normalized evidence bytes exactly as uploaded, not reserialized JSON.
    import io,zipfile
    with zipfile.ZipFile(io.BytesIO(raw)) as z:evidence_digest=hashlib.sha256(z.read("evidence.json")).hexdigest()
    pages=json.loads(subprocess.check_output(["gh","api","--paginate","--slurp",
        "repos/"+os.environ["GITHUB_REPOSITORY"]+"/issues/38/comments?per_page=100"],
        stderr=subprocess.DEVNULL))
    comments=[comment for page in pages for comment in page]
    receipts=[]
    for comment in comments:
        try:receipt=json.loads(comment.get("body",""))
        except (ValueError,TypeError):continue
        if isinstance(receipt,dict) and receipt.get("request_id")==request:
            receipts.append((comment,receipt))
    for login in (c["operator"],c["reviewer"]):
        selected=[(comment,receipt) for comment,receipt in receipts
                  if comment.get("user",{}).get("login","").lower()==login.lower()]
        require(selected,"independent operator/reviewer receipt missing")
        comment,receipt=selected[-1]
        validate_receipt(receipt,comment["user"]["login"],comment["user"].get("type"),
                         login,pr["user"]["login"],qa["user"]["login"],data,artifact_id,evidence_digest)
    run_url="https://github.com/"+os.environ["GITHUB_REPOSITORY"]+"/actions/runs/"+c["run_id"]
    status=dict(state="success",context="aronexa/central-qa/"+PLAN,
                description="request="+request+"; qa=success; release-not-authorized",target_url=run_url)
    Path("status.json").write_text(json.dumps(status)+"\n",encoding="utf-8")
    receipt=dict(body="Independent test-only WIN11P evidence verified. Source "+c["source_sha"]+
        "; QA "+c["qa_sha"]+"; request "+request+"; artifact "+str(artifact_id)+
        "; evidence SHA256 "+evidence_digest+"; reviewer "+c["reviewer"]+
        "; operator "+c["operator"]+". "+run_url+". Customer release remains NOT_READY.")
    Path("receipt.json").write_text(json.dumps(receipt)+"\n",encoding="utf-8")
    print("WIN11P exact-artifact independent receipts verified; status payload prepared")

def main():
    parser=argparse.ArgumentParser()
    sub=parser.add_subparsers(dest="command",required=True)
    p=sub.add_parser("prepare");p.add_argument("--app",required=True);p.add_argument("--output",required=True)
    p=sub.add_parser("report")
    for flag in ("artifact-id","source-bundle-sha","qa-archive-sha"):p.add_argument("--"+flag,required=True)
    args=parser.parse_args()
    try:
        (prepare if args.command=="prepare" else report)(args)
    except (ValueError,OSError,subprocess.SubprocessError,KeyError,TypeError):
        # Never echo inputs, API bodies, paths or underlying subprocess output.
        print("WIN11P control refused missing, stale or unauthorized evidence",file=sys.stderr)
        return 1
    return 0

if __name__=="__main__":raise SystemExit(main())
