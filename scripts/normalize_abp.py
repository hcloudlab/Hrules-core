#!/usr/bin/env python3
"""Strict ABP-domain normalizer. Unsupported syntax is rejected, never broadened."""
from __future__ import annotations
import argparse,json,re
from pathlib import Path
DOMAIN=re.compile(r"^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")
def classify(line:str):
 raw=line.strip()
 if not raw or raw.startswith(("!","#","[")):return ("ignore",None,"comment_or_blank",None)
 if raw.startswith("@@"):return ("reject",None,"exception_rule",None)
 if "##" in raw or "#@#" in raw or "#?#" in raw:return ("reject",None,"cosmetic_rule",None)
 if raw.startswith("/") and raw.endswith("/"):return ("reject",None,"regex_rule",None)
 if "$" in raw:return ("reject",None,"optioned_rule",None)
 if raw.startswith("||") and raw.endswith("^"):
  value=raw[2:-1].lower()
  return ("accept",{"type":"domain_suffix","value":value},"abp_domain_anchor","SAFE_DEGRADE") if DOMAIN.fullmatch(value) else ("reject",None,"invalid_domain",None)
 value=raw.lower().rstrip(".")
 if DOMAIN.fullmatch(value):return ("accept",{"type":"domain_suffix","value":value},"plain_domain","EXACT")
 return ("reject",None,"unsupported_syntax",None)
def normalize(lines):
 accepted=[];rejected=[];seen={}
 for n,line in enumerate(lines,1):
  state,match,reason,lowering=classify(line)
  if state=="accept":
   key=(match["type"],match["value"])
   if key not in seen:
    rec={**match,"source_syntax":reason,"semantic_lowering":lowering};accepted.append(rec);seen[key]=rec
   elif lowering=="SAFE_DEGRADE":seen[key]["semantic_lowering"]="SAFE_DEGRADE"
  elif state=="reject":rejected.append({"line":n,"reason":reason,"input":line.rstrip("\n")})
 return accepted,rejected
def main()->int:
 p=argparse.ArgumentParser();p.add_argument("input");p.add_argument("--out",required=True);p.add_argument("--rejects",required=True);p.add_argument("--max-reject-ratio",type=float,default=.05)
 a=p.parse_args();accepted,rejected=normalize(Path(a.input).read_text(encoding="utf-8",errors="replace").splitlines());classified=len(accepted)+len(rejected);ratio=len(rejected)/classified if classified else 1
 Path(a.rejects).write_text(json.dumps(rejected,ensure_ascii=False,indent=2)+"\n")
 if not accepted or ratio>a.max_reject_ratio:print(f"REFUSED ABP normalization: accepted={len(accepted)} rejected={len(rejected)} ratio={ratio:.3f}");return 1
 Path(a.out).write_text(json.dumps({"matches":accepted},ensure_ascii=False,indent=2)+"\n");print(f"NORMALIZED accepted={len(accepted)} rejected={len(rejected)} ratio={ratio:.3f}");return 0
if __name__=="__main__":raise SystemExit(main())
