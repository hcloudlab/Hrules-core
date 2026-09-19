#!/usr/bin/env python3
import json,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 with tempfile.TemporaryDirectory() as td:
  d=Path(td); gated=d/"g.json"; cs=d/"c"; cs.mkdir(); out=d/"o.json"
  item={"id":"blk-aaaaaaaaaaaaaaaa","match":{"type":"domain_suffix","value":"ads.example"},"review":{"decision":"block"}}
  gated.write_text(json.dumps({"promotable":[item]}))
  (cs/"a.json").write_text(json.dumps({"schema_version":1,"candidate_id":item["id"],"ownership":"dedicated_third_party","purpose":"advertising","classifier":"fixture","classified_at":"2026-09-18","evidence":["fixture"],"reason":"fixture"}))
  subprocess.run([sys.executable,str(ROOT/"scripts/gate_blocking_classification.py"),"--gated",str(gated),"--classifications",str(cs),"--out",str(out)],check=True,cwd=ROOT)
  doc=json.loads(out.read_text()); assert len(doc["ready"])==1 and doc["status"]=="classification_gated"
 print("All Blocking classification gate tests passed")
if __name__=="__main__": main()
