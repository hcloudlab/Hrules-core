#!/usr/bin/env python3
"""Convert reviewed Blocking candidates into a canonical-module proposal.

This script never edits rules/blocking/blocking.yaml. It emits a proposal that must
still pass canonical validation and an explicit maintainer merge.
"""
from __future__ import annotations
import argparse, json
from datetime import date
from pathlib import Path
import yaml

def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("--gated",required=True); p.add_argument("--out",required=True)
    p.add_argument("--module-template",default="rules/blocking/blocking.yaml")
    a=p.parse_args()
    gated=json.loads(Path(a.gated).read_text())
    template=yaml.safe_load(Path(a.module_template).read_text()) or {}
    rules=[]
    for item in gated.get("promotable",[]):
        review=item["review"]; sources=item.get("sources",[])
        level="corroborated" if len(set(sources))>=2 else "candidate"
        rules.append({
          "id": item["id"],
          "match": item["match"],
          "ownership": "dedicated_third_party",
          "purpose": "advertising",
          "provenance": {"kind":"upstream","source":",".join(sorted(set(sources))),"reference":item["id"],"observed_at":review["reviewed_at"]},
          "evidence": {"level":level,"methods":["upstream_ruleset","manual_review"]},
          "validation": {"state":"partial","last_tested":review["reviewed_at"],"tests":["false_positive_review"]},
          "conflicts": [],
          "notes": "Promotion proposal only; routing_match and release-policy evidence are still required before publication."
        })
    proposal={
      "schema_version":1,
      "module":{**template["module"],"status":"research"},
      "release_policy":template.get("release_policy",{}),
      "rules":rules
    }
    Path(a.out).parent.mkdir(parents=True,exist_ok=True)
    Path(a.out).write_text(yaml.safe_dump(proposal,sort_keys=False,allow_unicode=True))
    print(f"PROPOSAL ONLY rules={len(rules)}; canonical source file unchanged")
    return 0
if __name__=="__main__": raise SystemExit(main())
