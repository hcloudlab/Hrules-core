#!/usr/bin/env python3
import json, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def check(n,c):
    if not c: raise AssertionError(n)
    print("PASS",n)
def main():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td); c=d/"c.json"; r=d/"risk.json"; out=d/"batch.json"
        items=[
          {"id":"blk-aaaaaaaaaaaaaaaa","match":{"type":"domain_suffix","value":"a.example.com"},"sources":["a","b"],"source_count":2,"root_domain":"example.com","root_concentration":2,"risk":{"tier":"low","score":0,"reasons":[]}},
          {"id":"blk-bbbbbbbbbbbbbbbb","match":{"type":"domain_suffix","value":"b.example.net"},"sources":["a"],"source_count":1,"root_domain":"example.net","root_concentration":1,"risk":{"tier":"low","score":2,"reasons":[]}},
          {"id":"blk-cccccccccccccccc","match":{"type":"domain_suffix","value":"c.dense.test"},"sources":["a","b"],"source_count":2,"root_domain":"dense.test","root_concentration":50,"risk":{"tier":"low","score":0,"reasons":[]}}
        ]
        c.write_text(json.dumps({"status":"review_only","candidates":items}))
        r.write_text(json.dumps({"status":"triage_only","samples":{"low":items,"medium":[],"high":[]}}))
        subprocess.run([sys.executable,str(ROOT/"scripts/build_blocking_review_batch.py"),"--candidates",str(c),"--risk",str(r),"--out",str(out),"--limit","10","--max-root-concentration","10","--require-multi-source"],check=True,cwd=ROOT)
        doc=json.loads(out.read_text())
        check("only low-risk corroborated low-concentration candidate selected",[x["id"] for x in doc["selected"]]==["blk-aaaaaaaaaaaaaaaa"])
        check("batch remains review-only",doc["status"]=="review_batch_only")
    print("All Blocking review batch tests passed")
if __name__=="__main__": main()
