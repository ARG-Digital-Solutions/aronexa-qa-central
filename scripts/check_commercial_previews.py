#!/usr/bin/env python3
import json, pathlib, re
root=pathlib.Path(__file__).resolve().parents[1]
specs={75:("COMM_V1_T01",13,"consultation"),78:("COMM_V1_T03",14,"smart-rx"),79:("COMM_V1_T04",15,"billing")}
for pr,(pid,issue,feature) in specs.items():
    p=root/"qa/commercial"/(pid+".json")
    d=json.loads(p.read_text())
    assert d["plan_id"]==pid and d["pr_number"]==pr and d["qa_issue"]==issue and d["feature"]==feature
    assert d["source_repository"]=="ARG-Digital-Solutions/aronexa-healthcare-platform" and d["base_branch"]=="main"
    assert re.fullmatch("[0-9a-f]{40}",d["approved_sha"])
    assert d["synthetic_only"] is True and d["independent_review_required"] is True and d["release_approved"] is False
    assert len(d["expected_paths"])==8 and len(set(d["expected_paths"]))==8
    assert all(isinstance(x,str) and not x.startswith("/") and ".." not in pathlib.PurePosixPath(x).parts for x in d["expected_paths"])
    for key in ("model_test","vite_config","preview_page"):
        assert d[key] and "/" not in d[key] if key!="model_test" else d[key].startswith("test/") and d[key].count("/")==1
    assert "frontend/"+d["model_test"] in d["expected_paths"]
    assert "frontend/"+d["vite_config"] in d["expected_paths"]
    assert "frontend/"+d["preview_page"] in d["expected_paths"]
    assert (root/"tests/commercial"/(feature+".spec.mjs")).is_file()
    print("Validated",pid)
