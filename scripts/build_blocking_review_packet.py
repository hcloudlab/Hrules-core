#!/usr/bin/env python3
"""Build a deterministic human-review packet from a bounded Blocking review batch."""
from __future__ import annotations
import argparse, json
from pathlib import Path

def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument("--batch",required=True)
    p.add_argument("--out-json",required=True)
    p.add_argument("--out-md",required=True)
    a=p.parse_args()
    doc=json.loads(Path(a.batch).read_text())
    policy=doc.get("policy",{})
    if doc.get("status")!="review_batch_only" or policy.get("tier")!="low" or not policy.get("require_exact_lowering"):
        raise SystemExit("REFUSED: review packet requires bounded low-risk EXACT batch")
    selected=doc.get("selected",[])
    if any(x.get("semantic_lowering")!="EXACT" or x.get("risk",{}).get("tier")!="low" for x in selected):
        raise SystemExit("REFUSED: batch contains non-EXACT or non-low-risk candidate")
    packet=[]
    for item in selected:
        packet.append({
            "candidate_id":item["id"],
            "match":item["match"],
            "sources":item.get("sources",[]),
            "source_count":item.get("source_count",0),
            "semantic_lowering":item.get("semantic_lowering"),
            "root_domain":item.get("root_domain"),
            "root_concentration":item.get("root_concentration"),
            "risk":item.get("risk",{}),
            "review_state":"pending",
            "classification_state":"pending",
            "runtime_validation_state":"pending",
            "license_gate_state":"pending"
        })
    out={"schema_version":1,"status":"human_review_required","count":len(packet),"candidates":packet}
    Path(a.out_json).parent.mkdir(parents=True,exist_ok=True)
    Path(a.out_json).write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
    lines=[
        "# Blocking v0.1 — EXACT candidate review packet",
        "",
        "This packet is generated from the bounded low-risk EXACT cohort. It is evidence for review, not a publication artifact.",
        "",
        "| # | Candidate | Match | Sources | Risk | Root concentration | Review | Classification | Runtime | License |",
        "|---:|---|---|---|---|---:|---|---|---|---|",
    ]
    for i,x in enumerate(packet,1):
        m=x["match"]
        sources=", ".join(x["sources"])
        tier=x["risk"].get("tier","")
        lines.append("| %d | \`%s\` | \`%s:%s\` | %s | %s | %s | pending | pending | pending | pending |" % (
            i, x["candidate_id"], m["type"], m["value"], sources, tier, x.get("root_concentration","")
        ))
    Path(a.out_md).parent.mkdir(parents=True,exist_ok=True)
    Path(a.out_md).write_text("\n".join(lines)+"\n")
    print("REVIEW PACKET candidates=%d" % len(packet))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
