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
    p.add_argument("--routing-match-validated",action="store_true")
    a=p.parse_args()
    gated=json.loads(Path(a.gated).read_text())
    template=yaml.safe_load(Path(a.module_template).read_text()) or {}
    rules=[]
    items=gated.get("ready", gated.get("promotable",[]))
    for item in items:
        review=item["review"]; sources=item.get("sources",[]); classification=item.get("classification")
        level="corroborated" if len(set(sources))>=2 else "candidate"
        rules.append({
          "id": item["id"],
          "match": item["match"],
          "ownership": classification["ownership"] if classification else "unknown",
          "purpose": classification["purpose"] if classification else "unknown",
          "provenance": {"kind":"upstream","source":",".join(sorted(set(sources))),"reference":item["id"],"observed_at":review["reviewed_at"]},
          "evidence": {"level":level,"methods":["upstream_ruleset","manual_review"]},
          "validation": {
              "state":"passed" if a.routing_match_validated else "partial",
              "last_tested":review["reviewed_at"],
              "tests":["false_positive_review","routing_match"] if a.routing_match_validated else ["false_positive_review"]
          },
          "conflicts": [],
          "notes": (
              "Promotion proposal only; routing_match is validated, but verified evidence and release-policy checks are still required before publication."
              if classification and a.routing_match_validated else
              "Promotion proposal only; routing_match, verified evidence and release-policy checks are still required before publication."
              if classification else
              "Promotion proposal only; ownership/purpose classification, routing_match and release-policy evidence are still required before publication."
          )
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
