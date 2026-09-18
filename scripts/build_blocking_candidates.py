#!/usr/bin/env python3
"""Build a review-only Blocking candidate set from guarded upstream snapshots."""
from __future__ import annotations
import argparse, hashlib, json
from collections import defaultdict
from pathlib import Path
import yaml
from scripts.normalize_abp import normalize

def sha(path: Path)->str: return hashlib.sha256(path.read_bytes()).hexdigest()
def existing_matchers(root: Path):
    found={}
    for path in sorted(root.rglob("*.yaml")):
        doc=yaml.safe_load(path.read_text()) or {}
        mid=doc.get("module",{}).get("id")
        if mid=="blocking": continue
        for r in doc.get("rules",[]):
            m=r.get("match",{}); key=(m.get("type"),str(m.get("value","")).lower())
            found.setdefault(key,[]).append({"module":mid,"rule":r.get("id")})
    return found
def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("--source",action="append",required=True,help="source_id=guarded_snapshot_path")
    p.add_argument("--rules",default="rules"); p.add_argument("--out",required=True); p.add_argument("--report",required=True)
    p.add_argument("--max-reject-ratio",type=float,default=.05); p.add_argument("--min-sources",type=int,default=1)
    a=p.parse_args(); provenance=defaultdict(list); rejected=[]; source_meta=[]
    for spec in a.source:
        sid,raw=spec.split("=",1); path=Path(raw)
        accepted,rej=normalize(path.read_text(encoding="utf-8",errors="replace").splitlines())
        classified=len(accepted)+len(rej); ratio=len(rej)/classified if classified else 1
        if not accepted or ratio>a.max_reject_ratio: raise SystemExit(f"REFUSED {sid}: accepted={len(accepted)} rejected={len(rej)} ratio={ratio:.3f}")
        for m in accepted: provenance[(m["type"],m["value"])].append(sid)
        rejected.extend({"source":sid,**x} for x in rej)
        source_meta.append({"id":sid,"path":str(path),"sha256":sha(path),"accepted":len(accepted),"rejected":len(rej),"reject_ratio":ratio})
    existing=existing_matchers(Path(a.rules)); candidates=[]; conflicts=[]
    for key,sources in sorted(provenance.items()):
        rec={"match":{"type":key[0],"value":key[1]},"sources":sorted(set(sources)),"source_count":len(set(sources))}
        if key in existing:
            conflicts.append({**rec,"existing":existing[key],"reason":"exact_existing_matcher"})
            continue
        if rec["source_count"]>=a.min_sources: candidates.append(rec)
    out={"schema_version":1,"status":"review_only","candidates":candidates}
    Path(a.out).parent.mkdir(parents=True,exist_ok=True); Path(a.out).write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
    report={"sources":source_meta,"candidate_count":len(candidates),"conflicts":conflicts,"rejected_count":len(rejected),"rejected":rejected}
    Path(a.report).parent.mkdir(parents=True,exist_ok=True); Path(a.report).write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print(f"REVIEW ONLY candidates={len(candidates)} conflicts={len(conflicts)} rejected={len(rejected)}")
    return 0
if __name__=="__main__": raise SystemExit(main())
