#!/usr/bin/env python3
"""Compare a fresh Blocking dry-run with the canonical research set."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import yaml

def key(rule):
    m=rule["match"]
    return (m["type"],m["value"].lower().rstrip("."))

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--candidates",required=True)
    p.add_argument("--canonical",default="rules/blocking/blocking.yaml")
    p.add_argument("--summary",required=True)
    p.add_argument("--out",required=True)
    a=p.parse_args()
    candidates=json.loads(Path(a.candidates).read_text()).get("candidates",[])
    canonical=yaml.safe_load(Path(a.canonical).read_text()).get("rules",[])
    summary=json.loads(Path(a.summary).read_text())
    fresh={key(x):x for x in candidates}
    current={key(x):x for x in canonical}
    missing=[{"id":r["id"],"match":r["match"]} for k,r in current.items() if k not in fresh]
    changed=[]
    for k,r in current.items():
        c=fresh.get(k)
        if not c: continue
        expected=set((r.get("provenance",{}).get("source") or "").split(","))
        actual=set(c.get("sources",[]))
        if expected and not expected.issubset(actual):
            changed.append({"id":r["id"],"match":r["match"],"expected_sources":sorted(expected),"actual_sources":sorted(actual)})
    out={
      "schema_version":1,
      "canonical_count":len(current),
      "fresh_candidate_count":len(fresh),
      "canonical_missing_from_fresh_candidates":missing,
      "canonical_source_regressions":changed,
      "upstream_conflict_count":summary.get("conflict_count"),
      "upstream_rejected_count":summary.get("rejected_count"),
      "status":"regression" if missing or changed else "stable"
    }
    Path(a.out).parent.mkdir(parents=True,exist_ok=True)
    Path(a.out).write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(out,ensure_ascii=False))
    if missing or changed:
        raise SystemExit("REFUSED: canonical Blocking upstream regression detected")
    return 0
if __name__=="__main__": raise SystemExit(main())
