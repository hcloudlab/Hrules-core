#!/usr/bin/env python3
"""Build bounded review batches from Blocking risk analysis and candidates."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

def rank(cid:str)->str: return hashlib.sha256(("batch:"+cid).encode()).hexdigest()

def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("--candidates",required=True); p.add_argument("--risk",required=True); p.add_argument("--out",required=True)
    p.add_argument("--tier",choices=["low","medium","high"],default="low"); p.add_argument("--limit",type=int,default=100)
    p.add_argument("--max-root-concentration",type=int,default=10); p.add_argument("--require-multi-source",action="store_true")
    a=p.parse_args()
    cand=json.loads(Path(a.candidates).read_text()).get("candidates",[])
    risk=json.loads(Path(a.risk).read_text())
    annotated=risk.get("candidates",[])
    if not annotated:
        raise SystemExit("REFUSED: risk analysis lacks full candidate annotations")
    eligible=[]
    for x in annotated:
        if x.get("risk",{}).get("tier") != a.tier: continue
        if x.get("root_concentration",10**9)>a.max_root_concentration: continue
        if a.require_multi_source and x.get("source_count",1)<2: continue
        eligible.append(x)
    eligible=sorted(eligible,key=lambda x:rank(x["id"]))[:a.limit]
    out={"schema_version":1,"status":"review_batch_only","policy":{
      "tier":a.tier,"limit":a.limit,"max_root_concentration":a.max_root_concentration,
      "require_multi_source":a.require_multi_source},"selected":eligible}
    Path(a.out).parent.mkdir(parents=True,exist_ok=True); Path(a.out).write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
    print(f"REVIEW BATCH ONLY selected={len(eligible)} tier={a.tier}")
    return 0
if __name__=="__main__": raise SystemExit(main())
