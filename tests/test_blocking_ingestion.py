#!/usr/bin/env python3
import json, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def check(n,c):
    if not c: raise AssertionError(n)
    print("PASS",n)

def main():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)
        (d/"a.txt").write_text("ads.example.com\nshared.example.com\nchild.service.example.com\nprotected.example.com\n@@||allow.example^\n")
        (d/"b.txt").write_text("ads.example.com\ntracker.example.com\n")
        rules=d/"rules"; rules.mkdir()
        (rules/"service.yaml").write_text("""schema_version: 1
module: {id: service, policy_class: ordinary_proxy}
rules:
  - id: shared
    match: {type: domain_suffix, value: shared.example.com}
  - id: service-parent
    match: {type: domain_suffix, value: service.example.com}
""")
        allow=d/"allow.yaml"
        allow.write_text("""schema_version: 1
status: research
entries:
  - match: {type: domain_suffix, value: protected.example.com}
    reason: protected test domain
    evidence: unit-test
""")
        out=d/"out.json"; report=d/"report.json"
        cmd=[
            sys.executable,str(ROOT/"scripts/build_blocking_candidates.py"),
            "--source",f"a={d/'a.txt'}","--source",f"b={d/'b.txt'}",
            "--rules",str(rules),"--out",str(out),"--report",str(report),
            "--allowlist",str(allow),"--max-reject-ratio","0.5"
        ]
        subprocess.run(cmd,check=True,cwd=ROOT)
        doc=json.loads(out.read_text()); rep=json.loads(report.read_text())
        by={x["match"]["value"]:x for x in doc["candidates"]}
        check("deduplicates and preserves corroboration",by["ads.example.com"]["source_count"]==2)
        check("keeps independent candidate","tracker.example.com" in by)
        check("blocks exact service collision from candidate set","shared.example.com" not in by)
        check("blocks hierarchical service overlap","child.service.example.com" not in by and len(rep["conflicts"])==2)
        check("protects explicit allowlist entries","protected.example.com" not in by and rep["allowlisted_count"]==1)
        check("candidate IDs are stable-shaped",all(x["id"].startswith("blk-") and len(x["id"])==20 for x in doc["candidates"]))
        check("preserves unsupported rule evidence",rep["rejected_count"]==1)
        check("output is review-only",doc["status"]=="review_only")
    print("All blocking ingestion tests passed")

if __name__=="__main__": main()
