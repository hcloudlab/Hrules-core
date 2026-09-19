#!/usr/bin/env python3
"""Build an importable Mihomo proof config from Hrules topology and canonical rules."""
from __future__ import annotations
import argparse
import importlib.util
from pathlib import Path
import re
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
    rx = re.compile(pattern)
    return [name for name in names if rx.search(name)]

def region_members(template: dict, node_names: list[str], manual_regions: dict | None = None) -> dict[str, list[str]]:
    """Classify nodes by explicit manual mapping first, then by node-name regex."""
    manual_regions = manual_regions or {}
    known = set(node_names)
    result: dict[str, list[str]] = {}
    for region in template.get("region_groups", []):
        selected: list[str] = []
        for name in manual_regions.get(region["id"], []) or []:
            if name not in known:
                raise ValueError(f"manual region {region['id']} references unknown proxy: {name}")
            if name not in selected:
                selected.append(name)
        for name in matching(node_names, region["filter"]):
            if name not in selected:
                selected.append(name)
        if selected:
            result[region["id"]] = selected
    return result

def build_groups(template: dict, node_names: list[str], manual_regions: dict | None = None) -> list[dict]:
    groups: list[dict] = []
    members = region_members(template, node_names, manual_regions)
    for region in template.get("region_groups", []):
        selected = members.get(region["id"], [])
        if not selected:
            continue
        groups.append({"name": region["name"], "type": "select", "proxies": selected})

    for system in template.get("system_groups", []):
        if system["id"] == "all":
            groups.append({"name": system["name"], "type": "select", "proxies": node_names})
        elif system["id"] in {"auto", "fallback", "load-balance"}:
            group = {
                "name": system["name"], "type": system["type"], "proxies": node_names,
                "url": system["test_url"], "interval": system["interval"],
            }
            if "tolerance" in system:
                group["tolerance"] = system["tolerance"]
            if "strategy" in system:
                group["strategy"] = system["strategy"]
            groups.append(group)

    existing = {g["name"] for g in groups}
    for user in template.get("user_groups", []):
        candidates = [x for x in user.get("candidates", []) if x in existing]
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
    for module in compiler.order_modules(compiler.load_modules(rules_root), policy):
        text = compiler.compile_module(module, "mihomo", include_research, policy)
        lines.extend(line for line in text.splitlines() if line.strip())
    lines.append("MATCH,🚀 漏网之鱼 [自选]")
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
        "mixed-port": 7890, "allow-lan": False, "mode": "rule", "log-level": "info",
        "proxies": nodes, "proxy-groups": build_groups(template, names),
        "rules": build_rules(Path(args.rules), Path(args.policy), args.include_research),
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(yaml.safe_dump(config, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print(f"WROTE {out}: proxies={len(nodes)} groups={len(config['proxy-groups'])} rules={len(config['rules'])}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
