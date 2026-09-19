#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "generators" / "build_mihomo_from_config.py"
spec = importlib.util.spec_from_file_location("real_builder", PATH)
real_builder = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(real_builder)


def check(name, condition):
    if not condition:
        raise AssertionError(name)
    print(f"PASS {name}")


def main():
    source = yaml.safe_load((ROOT / "tests/fixtures/mihomo-source-config.yaml").read_text(encoding="utf-8"))
    template = yaml.safe_load((ROOT / "templates/mihomo/v0.1.yaml").read_text(encoding="utf-8"))
    out = real_builder.build(source, template, ROOT / "rules", ROOT / "policies/v0.1.yaml", True)

    check("all real proxies preserved", out["proxies"] == source["proxies"])
    check("source groups replaced by Hrules topology", "原机场默认" not in {g["name"] for g in out["proxy-groups"]})
    check("source rules replaced by Hrules routing", 'MATCH,"原机场默认"' not in out["rules"])
    check("source mixed port preserved", out["mixed-port"] == 7897)
    check("source allow-lan preserved", out["allow-lan"] is True)
    check("DNS preserved", out["dns"] == source["dns"])
    check("unknown runtime key external-ui preserved", out["external-ui"] == source["external-ui"])
    check("unknown runtime key keep-alive-interval preserved", out["keep-alive-interval"] == source["keep-alive-interval"])
    check("source rule-providers removed when Hrules owns routing", "rule-providers" not in out)
    names = {g["name"] for g in out["proxy-groups"]}
    check("all five region groups discovered", all(x in names for x in ["🇺🇸 美国 [系统]", "🇯🇵 日本 [系统]", "🇸🇬 新加坡 [系统]", "🇭🇰 香港 [系统]", "🇹🇼 台湾 [系统]"]))
    check("Hrules default rule present", out["rules"][-1] == "MATCH,🚀 默认代理 [自选]")
    print("All real-config builder tests passed")


if __name__ == "__main__":
    main()
