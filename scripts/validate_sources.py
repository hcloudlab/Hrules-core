#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from pathlib import Path
import yaml
from jsonschema import Draft202012Validator,FormatChecker
def main()->int:
 root=Path(__file__).resolve().parents[1]; path=Path(sys.argv[1]) if len(sys.argv)>1 else root/"sources/registry.yaml"
 doc=yaml.safe_load(path.read_text()) or {}; schema=json.loads((root/"schemas/source-registry.schema.json").read_text())
 errs=sorted(Draft202012Validator(schema,format_checker=FormatChecker()).iter_errors(doc),key=lambda e:list(e.path))
 if errs:
  for e in errs:print("FAIL source registry "+"/".join(map(str,e.path))+": "+e.message)
  return 1
 for sid,s in doc.get("sources",{}).items():
  if s.get("role")=="blocking_candidate":
   missing=[x for x in ("upstream","ingestion") if x not in s]
   if missing:print(f"FAIL {sid}: blocking_candidate missing {','.join(missing)}");return 1
   if s.get("license")=="review_required" and s["ingestion"].get("redistribution_review")!="required":
    print(f"FAIL {sid}: unresolved license must require redistribution review");return 1
   ing=s.get("ingestion",{})
   if ing.get("redistribution_review")=="cleared" and ing.get("attribution_required") and not ing.get("attribution_notice"):
    print(f"FAIL {sid}: cleared redistribution with attribution requirement needs attribution_notice");return 1
 print(f"PASS source registry: {len(doc.get('sources',{}))} sources");return 0
if __name__=="__main__":raise SystemExit(main())
