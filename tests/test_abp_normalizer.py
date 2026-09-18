#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.normalize_abp import classify,normalize
def check(n,c):
 if not c:raise AssertionError(n)
 print("PASS",n)
def main():
 s,m,_,lower=classify("ads.example.com");check("plain domain exact",s=="accept" and lower=="EXACT")
 s,m,_,lower=classify("||tracker.example.com^");check("ABP anchor safe degrade",s=="accept" and m["value"]=="tracker.example.com" and lower=="SAFE_DEGRADE")
 for value in ["@@||example.com^","||example.com^$third-party","/ads[0-9]+/","example.com##.ad","*example.com*"]:check("unsafe syntax rejected: "+value,classify(value)[0]=="reject")
 accepted,rejected=normalize(["example.com","example.com","||ads.example.com^","@@||allow.example^"])
 check("deduplicates accepted matchers",len(accepted)==2);check("preserves lowering evidence",accepted[1]["semantic_lowering"]=="SAFE_DEGRADE");check("preserves rejection audit",len(rejected)==1 and rejected[0]["reason"]=="exception_rule")
 print("All ABP normalizer tests passed")
if __name__=="__main__":main()
