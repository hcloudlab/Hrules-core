#!/usr/bin/env python3
"""Run guarded real-upstream Blocking ingestion without canonical promotion."""
from __future__ import annotations
import argparse, json, subprocess, sys
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[1]

def main()->int:
    p=argparse.ArgumentParser(); p.add_argument("--source",action="append",default=[])
    p.add_argument("--out-dir",default="build/blocking-dry-run"); p.add_argument("--max-reject-ratio",type=float,default=.98)
    a=p.parse_args(); registry=yaml.safe_load((ROOT/"sources/registry.yaml").read_text())["sources"]
    ids=a.source or ["easylist_china","adrules_adblock_list"]; out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True)
    specs=[]
    for sid in ids:
        src=registry[sid]; url=src["upstream"]["raw_url"]; snap=out/f"{sid}.txt"; meta=out/f"{sid}.meta.json"
        cmd=[sys.executable,str(ROOT/"scripts/upstream_guard.py"),url,"--out",str(snap),"--meta",str(meta),"--min-bytes","1024","--min-entries","10"]
        prev=ROOT/"sources"/"snapshots"/f"{sid}.meta.json"
        if prev.exists(): cmd += ["--previous-meta",str(prev)]
        subprocess.run(cmd,check=True,cwd=ROOT); specs += ["--source",f"{sid}={snap}"]
    candidates=out/"candidates.json"; report=out/"report.json"
    subprocess.run([sys.executable,str(ROOT/"scripts/build_blocking_candidates.py"),*specs,"--out",str(candidates),"--report",str(report),"--max-reject-ratio",str(a.max_reject_ratio)],check=True,cwd=ROOT)
    rep=json.loads(report.read_text()); doc=json.loads(candidates.read_text())
    summary={"sources":rep["sources"],"candidate_count":len(doc["candidates"]),"conflict_count":len(rep["conflicts"]),"allowlisted_count":rep["allowlisted_count"],"rejected_count":rep["rejected_count"]}
    (out/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(summary,ensure_ascii=False))
    return 0
if __name__=="__main__": raise SystemExit(main())
