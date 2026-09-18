#!/usr/bin/env python3
"""Build a review-only Blocking candidate set from guarded upstream snapshots."""
from __future__ import annotations
import argparse, hashlib, json, sys
from collections import defaultdict
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.normalize_abp import normalize

def sha(path: Path)->str: return hashlib.sha256(path.read_bytes()).hexdigest()
def candidate_id(match_type: str, value: str)->str:
    return "blk-" + hashlib.sha256(f"{match_type}:{value}".encode()).hexdigest()[:16]

def domain_relation(a: tuple[str,str], b: tuple[str,str]) -> str | None:
    at,av=a[0],a[1].lower(); bt,bv=b[0],b[1].lower()
    if at not in {"domain","domain_suffix"} or bt not in {"domain","domain_suffix"}:
        return None
    if at==bt and av==bv: return "exact"
    if at=="domain_suffix" and (bv==av or bv.endswith("." + av)): return "a_contains_b"
    if bt=="domain_suffix" and (av==bv or av.endswith("." + bv)): return "b_contains_a"
    return None

def load_allowlist(path: Path):
    if not path.exists(): return []
    doc=yaml.safe_load(path.read_text()) or {}
    return doc.get("entries",[])
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
    p.add_argument("--allowlist",default="sources/blocking-allowlist.yaml")
    p.add_argument("--max-reject-ratio",type=float,default=.05); p.add_argument("--min-sources",type=int,default=1)
    a=p.parse_args(); provenance=defaultdict(list); semantics=defaultdict(set); rejected=[]; source_meta=[]
    for spec in a.source:
        sid,raw=spec.split("=",1); path=Path(raw)
        accepted,rej=normalize(path.read_text(encoding="utf-8",errors="replace").splitlines())
        classified=len(accepted)+len(rej); ratio=len(rej)/classified if classified else 1
        if not accepted or ratio>a.max_reject_ratio: raise SystemExit(f"REFUSED {sid}: accepted={len(accepted)} rejected={len(rej)} ratio={ratio:.3f}")
        for m in accepted:
            key=(m["type"],m["value"])
            provenance[key].append(sid)
            semantics[key].add(m.get("semantic_lowering","EXACT"))
        rejected.extend({"source":sid,**x} for x in rej)
        source_meta.append({"id":sid,"path":str(path),"sha256":sha(path),"accepted":len(accepted),"rejected":len(rej),"reject_ratio":ratio})
    existing=existing_matchers(Path(a.rules)); allowlist=load_allowlist(Path(a.allowlist)); candidates=[]; conflicts=[]; allowlisted=[]
    for key,sources in sorted(provenance.items()):
        rec={"id":candidate_id(key[0],key[1]),"match":{"type":key[0],"value":key[1]},"sources":sorted(set(sources)),"source_count":len(set(sources)),"semantic_lowering":"SAFE_DEGRADE" if "SAFE_DEGRADE" in semantics[key] else "EXACT"}
        protected=False
        for item in allowlist:
            m=item.get("match",{}); rel=domain_relation(key,(m.get("type"),str(m.get("value","")).lower()))
            if rel:
                allowlisted.append({**rec,"allowlist":item,"relation":rel,"reason":"protected_by_allowlist"})
                protected=True; break
        if protected: continue

        collision=[]
        for ex_key, owners in existing.items():
            rel=domain_relation(key, ex_key)
            if rel:
                collision.append({"existing_match":{"type":ex_key[0],"value":ex_key[1]},"owners":owners,"relation":rel})
        if collision:
            conflicts.append({**rec,"existing":collision,"reason":"overlap_existing_matcher"})
            continue
        if rec["source_count"]>=a.min_sources: candidates.append(rec)
    out={"schema_version":1,"status":"review_only","candidates":candidates}
    Path(a.out).parent.mkdir(parents=True,exist_ok=True); Path(a.out).write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
    report={"sources":source_meta,"candidate_count":len(candidates),"allowlisted_count":len(allowlisted),"allowlisted":allowlisted,"conflicts":conflicts,"rejected_count":len(rejected),"rejected":rejected}
    Path(a.report).parent.mkdir(parents=True,exist_ok=True); Path(a.report).write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print(f"REVIEW ONLY candidates={len(candidates)} allowlisted={len(allowlisted)} conflicts={len(conflicts)} rejected={len(rejected)}")
    return 0
if __name__=="__main__": raise SystemExit(main())
