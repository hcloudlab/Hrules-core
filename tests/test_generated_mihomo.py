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

    crypto = "💰 虚拟货币 [自选]"
    check("Coinbase routed to crypto group", f"DOMAIN-SUFFIX,coinbase.com,{crypto}" in rules)
    check("Binance routed to crypto group", f"DOMAIN-SUFFIX,binance.com,{crypto}" in rules)
    check("OKX routed to crypto group", f"DOMAIN-SUFFIX,okx.com,{crypto}" in rules)
    check("Bybit routed to crypto group", f"DOMAIN-SUFFIX,bybit.com,{crypto}" in rules)
    check("Kraken routed to crypto group", f"DOMAIN-SUFFIX,kraken.com,{crypto}" in rules)

    banking = "🏦 美国银行 [自选]"
    check("Bank of America routed to US banking group", f"DOMAIN-SUFFIX,bankofamerica.com,{banking}" in rules)
    check("Chase routed to US banking group", f"DOMAIN-SUFFIX,chase.com,{banking}" in rules)
    check("Wells Fargo routed to US banking group", f"DOMAIN-SUFFIX,wellsfargo.com,{banking}" in rules)
    check("Wells Fargo media candidate routed to US banking group", f"DOMAIN-SUFFIX,wellsfargomedia.com,{banking}" in rules)
    check("Wells Fargo exact wf.com auth candidate routed to US banking group", f"DOMAIN,connect.secure.wf.com,{banking}" in rules)
    check("Citi routed to US banking group", f"DOMAIN-SUFFIX,citi.com,{banking}" in rules)
    check("Capital One routed to US banking group", f"DOMAIN-SUFFIX,capitalone.com,{banking}" in rules)
    check("American Express routed to US banking group", f"DOMAIN-SUFFIX,americanexpress.com,{banking}" in rules)

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
    check("Crypto group exists", crypto in groups)
    check("Crypto excludes cross-region global auto", "♻️ 自动选择 [系统]" not in groups[crypto]["proxies"])
    check("Crypto has at least one usable choice", bool(groups[crypto]["proxies"]))
    check("US banking group exists", banking in groups)
    check("US banking excludes cross-region global auto", "♻️ 自动选择 [系统]" not in groups[banking]["proxies"])
    check("US banking has at least one usable choice", bool(groups[banking]["proxies"]))

    print("All generated Mihomo routing assertions passed")


if __name__ == "__main__":
    main()
