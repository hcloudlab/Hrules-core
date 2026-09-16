#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build/provider-proof/hrules-mihomo-provider-v0.1.yaml"


def check(name, condition):
    if not condition:
        raise AssertionError(name)
    print(f"PASS {name}")


def main():
    subprocess.run([
        sys.executable, str(ROOT / "generators/build_mihomo_provider_proof.py"),
        "--include-research", "--out", str(OUT)
    ], cwd=ROOT, check=True)

    cfg = yaml.safe_load(OUT.read_text(encoding="utf-8"))
    providers = cfg["rule-providers"]
    rules = cfg["rules"]

    check("youtube provider exists", providers["hrules-youtube"]["behavior"] == "domain")
    check("cn provider exists", providers["hrules-cn"]["behavior"] == "domain")
    check("youtube uses RULE-SET", "RULE-SET,hrules-youtube,📺 YouTube [自选]" in rules)
    check("cn uses RULE-SET", "RULE-SET,hrules-cn,DIRECT" in rules)
    check("youtube is not duplicated inline", not any(r.startswith("DOMAIN-SUFFIX,youtube.com,") for r in rules))
    check("cn is not duplicated inline", not any(r.startswith("DOMAIN-SUFFIX,cn,") for r in rules))
    check("MATCH remains final", rules[-1] == "MATCH,🚀 默认代理 [自选]")
    check("provider files copied", (OUT.parent / "providers/youtube.yaml").exists() and (OUT.parent / "providers/cn.yaml").exists())
    print("All Mihomo provider-mode proof tests passed")


if __name__ == "__main__":
    main()
