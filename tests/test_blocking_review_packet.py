#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td); batch=d/"batch.json"; outj=d/"packet.json"; outm=d/"packet.md"
        batch.write_text(json.dumps({"selected":[{
            "id":"blk-aaaaaaaaaaaaaaaa",
            "match":{"type":"domain","value":"ads.example.com"},
            "sources":["a","b"],"source_count":2,"semantic_lowering":"EXACT",
            "root_domain":"example.com","root_concentration":2,
            "risk":{"tier":"low","score":0,"reasons":[]}
        }]}))
        subprocess.run([sys.executable,str(ROOT/"scripts/build_blocking_review_packet.py"),
                        "--batch",str(batch),"--out-json",str(outj),"--out-md",str(outm)],check=True,cwd=ROOT)
        doc=json.loads(outj.read_text())
        assert doc["status"]=="human_review_required"
        assert doc["count"]==1
        item=doc["candidates"][0]
        assert item["match"]["type"]=="domain"
        assert item["semantic_lowering"]=="EXACT"
        assert item["review_state"]=="pending"
        assert "ads.example.com" in outm.read_text()
    print("All Blocking review packet tests passed")

if __name__=="__main__":
    main()
