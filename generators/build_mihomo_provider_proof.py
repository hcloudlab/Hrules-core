#!/usr/bin/env python3
"""Build a Mihomo proof config that consumes generated Hrules rule providers."""
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


builder = load_module(ROOT / "generators/build_mihomo.py", "build_mihomo")
compiler = load_module(ROOT / "generators/compile_rules.py", "compile_rules")


def load(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def build_inline_rules(rules_root: Path, policy_path: Path, include_research: bool) -> list[str]:
    policy = load(policy_path)
    lines: list[str] = []
    for module in compiler.load_modules(rules_root):
        module_id = module["module"]["id"]
        if module_id in {"youtube", "cn"}:
            continue
        text = compiler.compile_module(module, "mihomo", include_research, policy)
        lines.extend(line for line in text.splitlines() if line.strip())
    return lines


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--template", default="templates/mihomo/v0.1.yaml")
    p.add_argument("--nodes", default="tests/fixtures/mihomo-nodes.yaml")
    p.add_argument("--rules", default="rules")
    p.add_argument("--policy", default="policies/v0.1.yaml")
    p.add_argument("--providers", default="build/providers/mihomo")
    p.add_argument("--out", default="build/provider-proof/hrules-mihomo-provider-v0.1.yaml")
    p.add_argument("--include-research", action="store_true")
    args = p.parse_args()

    template = load(Path(args.template))
    nodes = builder.load_nodes(Path(args.nodes))
    names = [x["name"] for x in nodes]

    out = Path(args.out)
    provider_dir = out.parent / "providers"
    provider_dir.mkdir(parents=True, exist_ok=True)
    for provider_id in ("youtube", "cn"):
        src = Path(args.providers) / f"{provider_id}.yaml"
        if not src.exists():
            raise FileNotFoundError(f"provider artifact missing: {src}")
        shutil.copyfile(src, provider_dir / src.name)

    rules = build_inline_rules(Path(args.rules), Path(args.policy), args.include_research)
    rules.extend([
        "RULE-SET,hrules-youtube,📺 YouTube [自选]",
        "RULE-SET,hrules-cn,DIRECT",
        "MATCH,🚀 默认代理 [自选]",
    ])

    config = {
        "mixed-port": 7890,
        "allow-lan": False,
        "mode": "rule",
        "log-level": "info",
        "proxies": nodes,
        "proxy-groups": builder.build_groups(template, names),
        "rule-providers": {
            "hrules-youtube": {
                "type": "file", "behavior": "domain", "format": "yaml",
                "path": "./providers/youtube.yaml",
            },
            "hrules-cn": {
                "type": "file", "behavior": "domain", "format": "yaml",
                "path": "./providers/cn.yaml",
            },
        },
        "rules": rules,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(yaml.safe_dump(config, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print(f"WROTE {out}: providers=2 groups={len(config['proxy-groups'])} rules={len(rules)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
