#!/usr/bin/env python3
import json, subprocess, sys, tempfile
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[1]
def check(n,c):
    if not c: raise AssertionError(n)
    print("PASS",n)
def main():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td); gated=d/"gated.json"; out=d/"proposal.yaml"
        gated.write_text(json.dumps({"schema_version":1,"status":"review_gated","promotable":[{
          "id":"blk-1111111111111111","match":{"type":"domain_suffix","value":"ads.example.com"},
          "sources":["a","b"],"source_count":2,
          "review":{"decision":"block","reviewed_at":"2026-09-17","reason":"fixture"}
        }],"withheld":[]}))
        subprocess.run([sys.executable,str(ROOT/"scripts/promote_blocking_candidates.py"),"--gated",str(gated),"--out",str(out)],check=True,cwd=ROOT)
        doc=yaml.safe_load(out.read_text()); r=doc["rules"][0]
        check("proposal remains research",doc["module"]["status"]=="research")
        check("corroborated source evidence preserved",r["evidence"]["level"]=="corroborated")
        check("review does not claim routing validation",r["validation"]["state"]=="partial" and r["validation"]["tests"]==["false_positive_review"])
        check("stable candidate ID becomes canonical rule ID",r["id"]=="blk-1111111111111111")
    print("All Blocking promotion tests passed")
if __name__=="__main__": main()
