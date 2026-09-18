#!/usr/bin/env python3
import json, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def check(n,c):
    if not c: raise AssertionError(n)
    print("PASS",n)
def main():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td); cp=d/"c.json"; out=d/"risk.json"
        candidates=[
          {"id":"blk-aaaaaaaaaaaaaaaa","match":{"type":"domain_suffix","value":"example.com"},"sources":["a"],"source_count":1},
          {"id":"blk-bbbbbbbbbbbbbbbb","match":{"type":"domain_suffix","value":"ads.example.net"},"sources":["a","b"],"source_count":2}
        ]
        candidates += [{"id":f"blk-{i:016x}","match":{"type":"domain_suffix","value":f"x{i}.dense.example.org"},"sources":["a"],"source_count":1} for i in range(60)]
        cp.write_text(json.dumps({"status":"review_only","candidates":candidates}))
        subprocess.run([sys.executable,str(ROOT/"scripts/analyze_blocking_risk.py"),"--candidates",str(cp),"--out",str(out),"--sample-size","5"],check=True,cwd=ROOT)
        doc=json.loads(out.read_text())
        check("root-domain block is high risk",any(x["match"]["value"]=="example.com" for x in doc["samples"]["high"]))
        check("root concentration detected",doc["top_root_concentrations"][0]["candidate_count"]==60)
        check("samples are bounded",all(len(v)<=5 for v in doc["samples"].values()))
        check("analysis remains triage-only",doc["status"]=="triage_only")
    print("All Blocking risk analysis tests passed")
if __name__=="__main__": main()
