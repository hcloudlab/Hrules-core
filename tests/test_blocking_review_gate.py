#!/usr/bin/env python3
import json, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def check(name, condition):
    if not condition: raise AssertionError(name)
    print("PASS", name)

def main():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td); reviews=d/"reviews"; reviews.mkdir()
        candidates={"schema_version":1,"status":"review_only","candidates":[
            {"id":"blk-1111111111111111","match":{"type":"domain_suffix","value":"ads.example.com"},"sources":["a","b"],"source_count":2},
            {"id":"blk-2222222222222222","match":{"type":"domain_suffix","value":"maybe.example.com"},"sources":["a"],"source_count":1}
        ]}
        cp=d/"candidates.json"; cp.write_text(json.dumps(candidates))
        (reviews/"approved.json").write_text(json.dumps({
            "schema_version":1,"candidate_id":"blk-1111111111111111","decision":"block","reviewer":"test",
            "reviewed_at":"2026-09-17","expires":None,"reason":"fixture approved",
            "checks":{"service_overlap_reviewed":True,"root_domain_reviewed":True,"false_positive_reviewed":True},
            "evidence":["fixture"]
        }))
        out=d/"gated.json"
        subprocess.run([sys.executable,str(ROOT/"scripts/gate_blocking_reviews.py"),"--candidates",str(cp),"--reviews",str(reviews),"--out",str(out)],check=True,cwd=ROOT)
        doc=json.loads(out.read_text())
        check("approved block review becomes promotable", [x["id"] for x in doc["promotable"]]==["blk-1111111111111111"])
        check("unreviewed candidate remains withheld", [x["id"] for x in doc["withheld"]]==["blk-2222222222222222"])
        check("gate output remains non-canonical", doc["status"]=="review_gated")
    print("All Blocking review gate tests passed")

if __name__=="__main__": main()
