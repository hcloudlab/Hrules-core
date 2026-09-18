#!/usr/bin/env python3
"""Attach explicit classification to reviewed Blocking candidates; fail closed."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from jsonschema import Draft202012Validator,FormatChecker
def load(p): return json.loads(Path(p).read_text())
def main():
 p=argparse.ArgumentParser(); p.add_argument("--gated",required=True); p.add_argument("--classifications",required=True); p.add_argument("--out",required=True); p.add_argument("--schema",default="schemas/blocking-classification.schema.json"); a=p.parse_args()
 doc=load(a.gated); by={x["id"]:x for x in doc.get("promotable",[])}
 v=Draft202012Validator(load(a.schema),format_checker=FormatChecker()); cls={}; failures=0
 for path in sorted(Path(a.classifications).glob("*.json")):
  x=load(path); errs=list(v.iter_errors(x))
  if errs: failures+=1; print(f"FAIL {path}: "+"; ".join(e.message for e in errs)); continue
  cid=x["candidate_id"]
  if cid not in by: failures+=1; print(f"FAIL {path}: unknown/non-promotable {cid}"); continue
  if cid in cls: failures+=1; print(f"FAIL {path}: duplicate {cid}"); continue
  cls[cid]=x
 ready=[]; withheld=[]
 for cid,item in sorted(by.items()):
  x=cls.get(cid)
  if x and x["ownership"]=="dedicated_third_party" and x["purpose"] in ("advertising","analytics","telemetry"):
   ready.append({**item,"classification":x})
  else: withheld.append({**item,"classification":x,"reason":"missing_or_non_publishable_classification"})
 out={"schema_version":1,"status":"classification_gated","ready":ready,"withheld":withheld}
 Path(a.out).write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n"); print(f"CLASSIFICATION GATE ready={len(ready)} withheld={len(withheld)} failures={failures}"); return 1 if failures else 0
if __name__=="__main__": raise SystemExit(main())
