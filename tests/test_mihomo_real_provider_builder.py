#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build/proof/hrules-mihomo-real-provider-fixture.yaml"


def check(name, condition):
    if not condition:
        raise AssertionError(name)
    print(f"PASS {name}")


def main():
    subprocess.run([
        sys.executable, str(ROOT / "generators/build_mihomo_from_config_providers.py"),
        str(ROOT / "tests/fixtures/mihomo-source-config.yaml"),
        "--include-research", "--out", str(OUT)
    ], cwd=ROOT, check=True)

    cfg = yaml.safe_load(OUT.read_text(encoding="utf-8"))
    source = yaml.safe_load((ROOT / "tests/fixtures/mihomo-source-config.yaml").read_text(encoding="utf-8"))
    check("all source proxies preserved", cfg["proxies"] == source["proxies"])
    check("source dns preserved", cfg.get("dns") == source.get("dns"))
    check("youtube provider wired", cfg["rule-providers"]["hrules-youtube"]["behavior"] == "domain")
    check("cn provider wired", cfg["rule-providers"]["hrules-cn"]["behavior"] == "domain")
    check("youtube rule-set present", "RULE-SET,hrules-youtube,📺 YouTube [自选]" in cfg["rules"])
    check("cn rule-set present", "RULE-SET,hrules-cn,DIRECT" in cfg["rules"])
    check("match final", cfg["rules"][-1] == "MATCH,🚀 默认代理 [自选]")
    check("provider files copied", (OUT.parent / "providers/youtube.yaml").exists() and (OUT.parent / "providers/cn.yaml").exists())
    print("All provider-mode real config transformer tests passed")


if __name__ == "__main__":
    main()
