#!/usr/bin/env python3
"""Assertions over a generated Mihomo proof configuration."""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build/proof/hrules-mihomo-v0.1.yaml"


def check(name, condition):
    if not condition:
        raise AssertionError(name)
    print(f"PASS {name}")


def main():
    subprocess.run(
        [sys.executable, str(ROOT / "generators/build_mihomo.py"), "--include-research", "--out", str(OUT)],
        cwd=ROOT,
        check=True,
    )
    cfg = yaml.safe_load(OUT.read_text(encoding="utf-8"))
    groups = {g["name"]: g for g in cfg["proxy-groups"]}
    rules = cfg["rules"]

    check("all proxy groups are non-empty", all(g.get("proxies") for g in cfg["proxy-groups"]))
    check("Claude routed to sensitive AI group", "DOMAIN-SUFFIX,claude.ai,🔐 Claude / OpenAI [自选]" in rules)
    check("OpenAI routed to sensitive AI group", "DOMAIN-SUFFIX,openai.com,🔐 Claude / OpenAI [自选]" in rules)
    check("ChatGPT routed to sensitive AI group", "DOMAIN-SUFFIX,chatgpt.com,🔐 Claude / OpenAI [自选]" in rules)
    check("OpenAI content routed to sensitive AI group", "DOMAIN-SUFFIX,oaiusercontent.com,🔐 Claude / OpenAI [自选]" in rules)
    check("Gemini routed to general AI group", "DOMAIN-SUFFIX,gemini.google.com,🤖 AI 服务 [自选]" in rules)
    check("YouTube routed to YouTube group", "DOMAIN-SUFFIX,youtube.com,📺 YouTube [自选]" in rules)
    check("Telegram routed to Telegram group", "DOMAIN-SUFFIX,telegram.org,💬 Telegram [自选]" in rules)
    check("Telegram short links routed to Telegram group", "DOMAIN-SUFFIX,t.me,💬 Telegram [自选]" in rules)
    check("Coinbase routed to crypto group", "DOMAIN-SUFFIX,coinbase.com,💰 虚拟货币 [自选]" in rules)
    check("IBKR routed to stocks group", "DOMAIN-SUFFIX,interactivebrokers.com,📈 美股 [自选]" in rules)
    check("TradingView inherits stocks user choice", "DOMAIN-SUFFIX,tradingview.com,📈 美股 [自选]" in rules)
    check("RFC1918 10/8 routed DIRECT", "IP-CIDR,10.0.0.0/8,DIRECT" in rules)
    check("RFC1918 172/12 routed DIRECT", "IP-CIDR,172.16.0.0/12,DIRECT" in rules)
    check("RFC1918 192.168/16 routed DIRECT", "IP-CIDR,192.168.0.0/16,DIRECT" in rules)
    check("IPv6 ULA routed DIRECT", "IP-CIDR6,fc00::/7,DIRECT" in rules)
    check("CN suffix routed DIRECT", "DOMAIN-SUFFIX,cn,DIRECT" in rules)
    check("MATCH is final rule", rules[-1] == "MATCH,🚀 默认代理 [自选]")

    sensitive = groups["🔐 Claude / OpenAI [自选]"]["proxies"]
    check("sensitive AI excludes cross-region global auto", "♻️ 自动选择 [系统]" not in sensitive)
    check("sensitive AI has at least one usable choice", bool(sensitive))
    check("YouTube group exists", "📺 YouTube [自选]" in groups)
    check("Telegram group exists", "💬 Telegram [自选]" in groups)

    print("All generated Mihomo routing assertions passed")


if __name__ == "__main__":
    main()
