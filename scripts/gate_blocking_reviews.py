#!/usr/bin/env python3
"""Validate Blocking review records and gate candidate promotion."""
from __future__ import annotations
import argparse, json
from datetime import date
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker

def load(path: Path): return json.loads(path.read_text(encoding="utf-8"))

def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("--candidates",required=True); p.add_argument("--reviews",required=True)
    p.add_argument("--schema",default="schemas/blocking-review.schema.json"); p.add_argument("--out",required=True)
    a=p.parse_args()
    candidates=load(Path(a.candidates)).get("candidates",[])
    by_id={x["id"]:x for x in candidates}
    schema=load(Path(a.schema)); v=Draft202012Validator(schema,format_checker=FormatChecker())
    reviews={}
    failures=0
    for path in sorted(Path(a.reviews).glob("*.json")):
        doc=load(path)
        errs=list(v.iter_errors(doc))
        if errs:
            failures+=1; print(f"FAIL {path}: "+"; ".join(e.message for e in errs)); continue
        cid=doc["candidate_id"]
        if cid not in by_id:
            failures+=1; print(f"FAIL {path}: unknown candidate_id {cid}"); continue
        if cid in reviews:
            failures+=1; print(f"FAIL {path}: duplicate review for {cid}"); continue
        if doc.get("expires") and date.fromisoformat(doc["expires"]) < date.today():
            failures+=1; print(f"FAIL {path}: expired review for {cid}"); continue
        reviews[cid]=doc
    promotable=[]; withheld=[]
    for cid,candidate in sorted(by_id.items()):
        review=reviews.get(cid)
        if review and review["decision"]=="block":
            promotable.append({**candidate,"review":review})
        else:
            withheld.append({**candidate,"review":review,"reason":"missing_or_non_block_review"})
    out={"schema_version":1,"status":"review_gated","promotable":promotable,"withheld":withheld}
    Path(a.out).parent.mkdir(parents=True,exist_ok=True); Path(a.out).write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
    print(f"REVIEW GATE promotable={len(promotable)} withheld={len(withheld)} failures={failures}")
    return 1 if failures else 0

if __name__=="__main__": raise SystemExit(main())
