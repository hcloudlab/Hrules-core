#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
from pathlib import Path
import yaml

ROOT=Path(__file__).resolve().parents[1]
COMPILER=ROOT/"generators"/"compile_rules.py"
spec=importlib.util.spec_from_file_location("compile_rules_first_batch",COMPILER)
compiler=importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(compiler)

def main():
    proposal=ROOT/"build"/"blocking-dry-run"/"first-canonical-proposal.yaml"
    doc=yaml.safe_load(proposal.read_text())
    ids={r["id"] for r in doc["rules"]}
    assert ids=={"blk-2b23a84a2c131be6","blk-16ba81838eba73bf"}, ids
    by={r["id"]:r for r in doc["rules"]}
    assert by["blk-2b23a84a2c131be6"]["match"]=={"type":"domain","value":"app.adjust.com"}
    assert by["blk-16ba81838eba73bf"]["match"]=={"type":"domain","value":"c.webengage.com"}
    policy=compiler.load_yaml(ROOT/"policies"/"v0.1.yaml")
    text=compiler.compile_module(doc,"mihomo",True,policy)
    assert "DOMAIN,app.adjust.com,REJECT" in text
    assert "DOMAIN,c.webengage.com,REJECT" in text
    print("PASS first reviewed Blocking batch lowers to exact REJECT matchers")

if __name__=="__main__":
    main()
