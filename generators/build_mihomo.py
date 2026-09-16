#!/usr/bin/env python3
"""Build an importable Mihomo proof config from Hrules topology and canonical rules.

The proof config uses local placeholder proxies supplied by --nodes. It is intended
for syntax/topology/routing validation, not public release.
"""
from __future__ import annotations
import argparse
import importlib.util
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
COMPILER_PATH = ROOT / "generators" / "compile_rules.py"
spec = importlib.util.spec_from_file_location("compile_rules", COMPILER_PATH)
compiler = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(compiler)


def load(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_nodes(path: Path) -> list[dict]:
    doc = load(path)
    nodes = doc.get("proxies", []) if isinstance(doc, dict) else []
    if not nodes:
        raise ValueError("node fixture must contain at least one proxy")
    return nodes


def matching(names: list[str], pattern: str) -> list[str]:
    import re
    rx = re.compile(pattern)
    return [name for name in names if rx.search(name)]


def build_groups(template: dict, node_names: list[str]) -> list[dict]:
    groups: list[dict] = []
    available_region_names: list[str] = []
    for region in template.get("region_groups", []):
        selected = matching(node_names, region["filter"])
        if not selected:
            continue
        available_region_names.append(region["name"])
        groups.append({
            "name": region["name"], "type": "url-test", "proxies": selected,
            "url": region["test_url"], "interval": region["interval"], "tolerance": region["tolerance"]
        })

    for system in template.get("system_groups", []):
        if system["id"] == "all":
            groups.append({"name": system["name"], "type": "select", "proxies": node_names})
        elif system["id"] == "auto":
            groups.append({"name": system["name"], "type": "url-test", "proxies": node_names,
                           "url": system["test_url"], "interval": system["interval"], "tolerance": system["tolerance"]})

    existing = {g["name"] for g in groups}
    for user in template.get("user_groups", []):
        candidates = [x for x in user.get("candidates", []) if x in existing]
        # Optional slots are deliberately omitted until a real non-empty slot is supplied.
        if not candidates:
            candidates = node_names[:1]
        groups.append({"name": user["name"], "type": "select", "proxies": candidates})
        existing.add(user["name"])

    fallback = template["fallback"]
    candidates = [x for x in fallback.get("candidates", []) if x in existing]
    if not candidates:
        candidates = node_names[:1]
    groups.append({"name": fallback["name"], "type": "select", "proxies": candidates})
    return groups


def build_rules(rules_root: Path, policy_path: Path, include_research: bool) -> list[str]:
    policy = load(policy_path)
    lines: list[str] = []
    for module in compiler.load_modules(rules_root):
        text = compiler.compile_module(module, "mihomo", include_research, policy)
        lines.extend(line for line in text.splitlines() if line.strip())
    lines.append("MATCH,🚀 默认代理 [自选]")
    return lines


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--template", default="templates/mihomo/v0.1.yaml")
    p.add_argument("--nodes", default="tests/fixtures/mihomo-nodes.yaml")
    p.add_argument("--rules", default="rules")
    p.add_argument("--policy", default="policies/v0.1.yaml")
    p.add_argument("--out", default="build/proof/hrules-mihomo-v0.1.yaml")
    p.add_argument("--include-research", action="store_true")
    args = p.parse_args()

    template = load(Path(args.template))
    nodes = load_nodes(Path(args.nodes))
    names = [x["name"] for x in nodes]
    config = {
        "mixed-port": 7890,
        "allow-lan": False,
        "mode": "rule",
        "log-level": "info",
        "proxies": nodes,
        "proxy-groups": build_groups(template, names),
        "rules": build_rules(Path(args.rules), Path(args.policy), args.include_research),
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(yaml.safe_dump(config, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print(f"WROTE {out}: proxies={len(nodes)} groups={len(config['proxy-groups'])} rules={len(config['rules'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
