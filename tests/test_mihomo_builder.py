#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "generators" / "build_mihomo.py"
spec = importlib.util.spec_from_file_location("build_mihomo", PATH)
builder = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(builder)

def check(name, condition):
    if not condition: raise AssertionError(name)
    print(f"PASS {name}")

def main():
    template = yaml.safe_load((ROOT / "templates/mihomo/v0.1.yaml").read_text(encoding="utf-8"))
    names = ["美国 Test-1","美国 Test-2","日本 Test-1","新加坡 Test-1","Premium-HK"]
    groups = builder.build_groups(template, names, {"hk":["Premium-HK"]})
    by_name = {g["name"]: g for g in groups}
    check("US region is a manual selector", by_name["🇺🇸 美国 [地区]"]["type"] == "select")
    check("US name classification", by_name["🇺🇸 美国 [地区]"]["proxies"] == ["美国 Test-1","美国 Test-2"])
    check("manual region assignment", by_name["🇭🇰 香港 [地区]"]["proxies"] == ["Premium-HK"])
    check("missing TW omitted", "🇹🇼 台湾 [地区]" not in by_name)
    sensitive = by_name["🔐 Claude / OpenAI [场景]"]["proxies"]
    check("Claude can select US region", "🇺🇸 美国 [地区]" in sensitive)
    check("Claude does not default to global auto", "♻️ 自动选择 [系统]" not in sensitive)
    check("fallback strategy exists", by_name["🛡️ 故障转移 [系统]"]["type"] == "fallback")
    check("load balance strategy exists", by_name["⚖️ 负载均衡 [系统]"]["type"] == "load-balance")
    check("fallback is a scene-independent entry", "🚀 漏网之鱼 [自选]" in by_name)
    try:
        builder.build_groups(template, names, {"us":["Missing-Node"]})
    except ValueError:
        print("PASS unknown manual proxy rejected")
    else:
        raise AssertionError("unknown manual proxy rejected")
    print("All Mihomo builder topology tests passed")

if __name__ == "__main__": main()
