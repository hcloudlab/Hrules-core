#!/usr/bin/env python3
"""Deterministic risk triage for review-only Blocking candidates."""
from __future__ import annotations
import argparse, json, hashlib
from collections import Counter, defaultdict
from pathlib import Path

MULTI_LABEL_SUFFIXES={"co.uk","com.cn","net.cn","org.cn","com.au","co.jp","com.hk","com.tw"}

def root_domain(value:str)->str:
    parts=value.lower().strip(".").split(".")
    if len(parts)<=2: return ".".join(parts)
    tail=".".join(parts[-2:])
    if tail in MULTI_LABEL_SUFFIXES and len(parts)>=3: return ".".join(parts[-3:])
    return tail

def stable_rank(cid:str)->str: return hashlib.sha256(cid.encode()).hexdigest()

def risk(candidate, root_count):
    value=candidate["match"]["value"]; root=root_domain(value); labels=value.count(".")+1
    reasons=[]; score=0
    if candidate.get("source_count",1)==1: score+=2; reasons.append("single_source")
    else: score-=1; reasons.append("multi_source_corroborated")
    if value==root: score+=4; reasons.append("registrable_root_block")
    elif labels<=3: score+=2; reasons.append("shallow_subdomain")
    if root_count[root]>=50: score+=2; reasons.append("high_root_concentration")
    if root_count[root]>=500: score+=2; reasons.append("very_high_root_concentration")
    if score>=6: tier="high"
    elif score>=3: tier="medium"
    else: tier="low"
    return tier,score,reasons,root

def main()->int:
    p=argparse.ArgumentParser(); p.add_argument("--candidates",required=True); p.add_argument("--out",required=True)
    p.add_argument("--sample-size",type=int,default=100)
    a=p.parse_args(); doc=json.loads(Path(a.candidates).read_text()); candidates=doc.get("candidates",[])
    roots=Counter(root_domain(x["match"]["value"]) for x in candidates)
    enriched=[]; tiers=Counter()
    for x in candidates:
        tier,score,reasons,root=risk(x,roots); tiers[tier]+=1
        enriched.append({**x,"root_domain":root,"root_concentration":roots[root],"risk":{"tier":tier,"score":score,"reasons":reasons}})
    samples={}
    for tier in ("high","medium","low"):
        pool=sorted((x for x in enriched if x["risk"]["tier"]==tier),key=lambda x:stable_rank(x["id"]))
        samples[tier]=pool[:a.sample_size]
    top=[{"root_domain":r,"candidate_count":n} for r,n in roots.most_common(100)]
    out={"schema_version":1,"status":"triage_only","candidate_count":len(enriched),"risk_counts":dict(tiers),
         "top_root_concentrations":top,"samples":samples}
    Path(a.out).parent.mkdir(parents=True,exist_ok=True); Path(a.out).write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
    print(f"TRIAGE ONLY candidates={len(enriched)} high={tiers['high']} medium={tiers['medium']} low={tiers['low']}")
    return 0
if __name__=="__main__": raise SystemExit(main())
