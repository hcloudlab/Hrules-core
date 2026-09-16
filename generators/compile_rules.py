#!/usr/bin/env python3
"""Hrules canonical -> client rule compiler prototype.

This prototype emits rule artifacts only, not complete client configurations.
Candidate/unvalidated records are included only with --include-research.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

TARGETS = ("mihomo", "shadowrocket", "sing-box")


def load_modules(root: Path) -> list[dict]:
    modules = []
    for path in sorted(list(root.rglob("*.yaml")) + list(root.rglob("*.yml"))):
        with path.open("r", encoding="utf-8") as fh:
            doc = yaml.safe_load(fh)
        if isinstance(doc, dict) and "module" in doc and "rules" in doc:
            doc["_path"] = str(path)
            modules.append(doc)
    return modules


def publishable(module: dict, rule: dict) -> bool:
    policy = module.get("release_policy", {})
    minimum = policy.get("minimum_evidence", "verified")
    rank = {"candidate": 0, "corroborated": 1, "verified": 2}
    evidence = rule.get("evidence", {}).get("level", "candidate")
    state = rule.get("validation", {}).get("state", "untested")
    ownership = rule.get("ownership")
    allowed = policy.get("allowed_ownership", [])
    return (
        rank.get(evidence, -1) >= rank.get(minimum, 2)
        and state == "passed"
        and (not allowed or ownership in allowed)
    )


def mihomo_line(rule: dict, group: str) -> str:
    m = rule["match"]
    mapping = {
        "domain": "DOMAIN",
        "domain_suffix": "DOMAIN-SUFFIX",
        "domain_keyword": "DOMAIN-KEYWORD",
        "ip_cidr": "IP-CIDR",
        "ip_cidr6": "IP-CIDR6",
        "process_name": "PROCESS-NAME",
        "process_path": "PROCESS-PATH",
    }
    if m["type"] not in mapping:
        raise ValueError(f"unsupported Mihomo matcher: {m['type']}")
    return f"{mapping[m['type']]},{m['value']},{group}"


def shadowrocket_line(rule: dict, group: str) -> str:
    m = rule["match"]
    mapping = {
        "domain": "DOMAIN",
        "domain_suffix": "DOMAIN-SUFFIX",
        "domain_keyword": "DOMAIN-KEYWORD",
        "ip_cidr": "IP-CIDR",
        "ip_cidr6": "IP-CIDR6",
        "process_name": "PROCESS-NAME",
    }
    if m["type"] not in mapping:
        raise ValueError(f"unsupported Shadowrocket matcher: {m['type']}")
    return f"{mapping[m['type']]},{m['value']},{group}"


def singbox_rule(rule: dict, outbound: str) -> dict:
    m = rule["match"]
    mapping = {
        "domain": "domain",
        "domain_suffix": "domain_suffix",
        "domain_keyword": "domain_keyword",
        "ip_cidr": "ip_cidr",
        "ip_cidr6": "ip_cidr",
        "process_name": "process_name",
        "process_path": "process_path",
    }
    if m["type"] not in mapping:
        raise ValueError(f"unsupported sing-box matcher: {m['type']}")
    return {mapping[m["type"]]: [m["value"]], "outbound": outbound}


def compile_module(module: dict, target: str, include_research: bool) -> str:
    module_id = module["module"]["id"]
    selected = [r for r in module["rules"] if include_research or publishable(module, r)]
    if target == "mihomo":
        return "\n".join(mihomo_line(r, f"HRULES::{module_id}") for r in selected) + ("\n" if selected else "")
    if target == "shadowrocket":
        return "\n".join(shadowrocket_line(r, f"HRULES::{module_id}") for r in selected) + ("\n" if selected else "")
    if target == "sing-box":
        obj = {"version": 1, "rules": [singbox_rule(r, f"HRULES::{module_id}") for r in selected]}
        return json.dumps(obj, ensure_ascii=False, indent=2) + "\n"
    raise ValueError(target)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rules", default="rules")
    parser.add_argument("--out", default="build/proof")
    parser.add_argument("--include-research", action="store_true")
    parser.add_argument("--target", choices=["all", *TARGETS], default="all")
    args = parser.parse_args()

    targets = TARGETS if args.target == "all" else (args.target,)
    out_root = Path(args.out)
    modules = load_modules(Path(args.rules))
    count = 0
    for module in modules:
        module_id = module["module"]["id"]
        for target in targets:
            ext = "json" if target == "sing-box" else "list"
            path = out_root / target / f"{module_id}.{ext}"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(compile_module(module, target, args.include_research), encoding="utf-8")
            print(f"WROTE {path}")
            count += 1
    print(f"Generated {count} artifact(s) from {len(modules)} module(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
