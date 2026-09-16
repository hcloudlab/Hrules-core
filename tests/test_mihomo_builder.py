#!/usr/bin/env python3
"""Topology/safety tests for the Mihomo proof builder."""
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
    if not condition:
        raise AssertionError(name)
    print(f"PASS {name}")


def main():
    template = yaml.safe_load((ROOT / "templates/mihomo/v0.1.yaml").read_text(encoding="utf-8"))
    names = ["美国 Test-1", "美国 Test-2", "日本 Test-1", "新加坡 Test-1"]
    groups = builder.build_groups(template, names)
    by_name = {g["name"]: g for g in groups}

    check("US region created", by_name["🇺🇸 美国 [系统]"]["proxies"] == ["美国 Test-1", "美国 Test-2"])
    check("missing HK region omitted", "🇭🇰 香港 [系统]" not in by_name)
    check("missing TW region omitted", "🇹🇼 台湾 [系统]" not in by_name)

    sensitive = by_name["🔐 Claude / OpenAI [自选]"]["proxies"]
    check("sensitive group references only existing groups", all(x in by_name or x in names for x in sensitive))
    check("empty optional ISP slot omitted", "🏠 ISP / 住宅 [自选]" not in sensitive)
    check("empty optional fixed slot omitted", "🎯 固定节点 [自选]" not in sensitive)
    check("sensitive group does not default to global auto", "♻️ 自动选择 [系统]" not in sensitive)

    no_region_groups = builder.build_groups(template, ["Node-A"])
    no_region = {g["name"]: g for g in no_region_groups}
    check("config survives no recognized regions", "🔐 Claude / OpenAI [自选]" in no_region)
    check("user group has non-empty fallback", bool(no_region["🔐 Claude / OpenAI [自选]"]["proxies"]))

    print("All Mihomo builder topology tests passed")


if __name__ == "__main__":
    main()
