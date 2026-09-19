#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys, tempfile
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/check_blocking_maintenance.py"

def run(candidates,canonical,summary):
    with tempfile.TemporaryDirectory() as td:
        td=Path(td); cp=td/"c.json"; yp=td/"b.yaml"; sp=td/"s.json"; out=td/"o.json"
        cp.write_text(json.dumps({"candidates":candidates})); yp.write_text(yaml.safe_dump({"rules":canonical})); sp.write_text(json.dumps(summary))
        r=subprocess.run([sys.executable,str(SCRIPT),"--candidates",str(cp),"--canonical",str(yp),"--summary",str(sp),"--out",str(out)],capture_output=True,text=True)
        return r,json.loads(out.read_text())

rule={"id":"x","match":{"type":"domain","value":"a.example"},"provenance":{"source":"s1,s2"}}
cand={"id":"c","match":{"type":"domain","value":"a.example"},"sources":["s1","s2"]}
r,d=run([cand],[rule],{"conflict_count":0,"rejected_count":0}); assert r.returncode==0 and d["status"]=="stable"
r,d=run([], [rule], {}); assert r.returncode!=0 and d["canonical_missing_from_fresh_candidates"]
r,d=run([{**cand,"sources":["s1"]}],[rule],{}); assert r.returncode!=0 and d["canonical_source_regressions"]
print("PASS Blocking maintenance regression checks")
