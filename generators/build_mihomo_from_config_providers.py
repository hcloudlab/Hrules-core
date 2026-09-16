#!/usr/bin/env python3
"""Transform an existing Mihomo config into an Hrules provider-mode test config."""
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import shutil
import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


base = load_module(ROOT / "generators/build_mihomo_from_config.py", "build_mihomo_from_config")
provider_proof = load_module(ROOT / "generators/build_mihomo_provider_proof.py", "build_mihomo_provider_proof")
builder = provider_proof.builder


def load(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def build(source: dict, template: dict, rules_root: Path, policy_path: Path, provider_root: Path, out: Path, include_research: bool) -> dict:
    proxies = source.get("proxies") or []
    if not isinstance(proxies, list) or not proxies:
        raise ValueError("source config must contain a non-empty top-level proxies list")
    names = [p.get("name") for p in proxies]
    if any(not isinstance(name, str) or not name for name in names):
        raise ValueError("every source proxy must have a non-empty name")
    if len(names) != len(set(names)):
        raise ValueError("source proxy names must be unique")

    provider_dir = out.parent / "providers"
    provider_dir.mkdir(parents=True, exist_ok=True)
    for provider_id in ("youtube", "cn"):
        src = provider_root / f"{provider_id}.yaml"
        if not src.exists():
            raise FileNotFoundError(f"provider artifact missing: {src}")
        shutil.copyfile(src, provider_dir / src.name)

    rules = provider_proof.build_inline_rules(rules_root, policy_path, include_research)
    rules.extend([
        "RULE-SET,hrules-youtube,📺 YouTube [自选]",
        "RULE-SET,hrules-cn,DIRECT",
        "MATCH,🚀 默认代理 [自选]",
    ])

    config = {
        "mixed-port": source.get("mixed-port", 7890),
        "allow-lan": source.get("allow-lan", False),
        "mode": "rule",
        "log-level": source.get("log-level", "info"),
        "proxies": proxies,
        "proxy-groups": builder.build_groups(template, names),
        "rule-providers": {
            "hrules-youtube": {"type": "file", "behavior": "domain", "format": "yaml", "path": "./providers/youtube.yaml"},
            "hrules-cn": {"type": "file", "behavior": "domain", "format": "yaml", "path": "./providers/cn.yaml"},
        },
        "rules": rules,
    }
    for key in base.PRESERVE_KEYS:
        if key in source:
            config[key] = source[key]
    return config


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("source")
    p.add_argument("--template", default="templates/mihomo/v0.1.yaml")
    p.add_argument("--rules", default="rules")
    p.add_argument("--policy", default="policies/v0.1.yaml")
    p.add_argument("--providers", default="build/providers/mihomo")
    p.add_argument("--out", default="build/local/hrules-mihomo-real-provider-test.yaml")
    p.add_argument("--include-research", action="store_true")
    args = p.parse_args()

    source = load(Path(args.source))
    if not isinstance(source, dict):
        raise ValueError("source config must be a YAML mapping")
    out = Path(args.out)
    config = build(source, load(Path(args.template)), Path(args.rules), Path(args.policy), Path(args.providers), out, args.include_research)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(yaml.safe_dump(config, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print(f"WROTE {out}: proxies={len(config['proxies'])} groups={len(config['proxy-groups'])} providers=2 rules={len(config['rules'])}")
    print("Source config was not modified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
