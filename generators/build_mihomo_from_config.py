#!/usr/bin/env python3
"""Build an Hrules Mihomo test config from an existing Mihomo/Clash config.

The source config supplies real proxies. Hrules owns the generated policy topology
and proof routing rules. The source file is never modified in place.
"""
from __future__ import annotations
import argparse
import importlib.util
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "generators" / "build_mihomo.py"
spec = importlib.util.spec_from_file_location("build_mihomo", PATH)
builder = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(builder)

PRESERVE_KEYS = (
    "ipv6", "external-controller", "secret", "unified-delay", "tcp-concurrent",
    "find-process-mode", "global-client-fingerprint", "profile", "geodata-mode",
    "geox-url", "dns", "tun", "sniffer", "hosts",
)


def load(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def build(source: dict, template: dict, rules_root: Path, policy_path: Path, include_research: bool) -> dict:
    proxies = source.get("proxies") or []
    if not isinstance(proxies, list) or not proxies:
        raise ValueError("source config must contain a non-empty top-level proxies list")
    names = [p.get("name") for p in proxies]
    if any(not isinstance(name, str) or not name for name in names):
        raise ValueError("every source proxy must have a non-empty name")
    if len(names) != len(set(names)):
        raise ValueError("source proxy names must be unique")

    out = {
        "mixed-port": source.get("mixed-port", 7890),
        "allow-lan": source.get("allow-lan", False),
        "mode": "rule",
        "log-level": source.get("log-level", "info"),
        "proxies": proxies,
        "proxy-groups": builder.build_groups(template, names),
        "rules": builder.build_rules(rules_root, policy_path, include_research),
    }
    for key in PRESERVE_KEYS:
        if key in source:
            out[key] = source[key]
    return out


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("source", help="existing Mihomo/Clash YAML containing real proxies")
    p.add_argument("--template", default="templates/mihomo/v0.1.yaml")
    p.add_argument("--rules", default="rules")
    p.add_argument("--policy", default="policies/v0.1.yaml")
    p.add_argument("--out", default="build/local/hrules-mihomo-real-test.yaml")
    p.add_argument("--include-research", action="store_true")
    args = p.parse_args()

    source_path = Path(args.source)
    source = load(source_path)
    if not isinstance(source, dict):
        raise ValueError("source config must be a YAML mapping")
    config = build(source, load(Path(args.template)), Path(args.rules), Path(args.policy), args.include_research)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(yaml.safe_dump(config, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print(f"WROTE {out}: proxies={len(config['proxies'])} groups={len(config['proxy-groups'])} rules={len(config['rules'])}")
    print("Source config was not modified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
