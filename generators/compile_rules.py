#!/usr/bin/env python3
"""Hrules canonical -> logical policy -> client rule compiler.

Two publication gates are intentionally distinct:
- rc: routing-identification evidence suitable for a public release candidate;
- stable: all module-declared required tests must be completed.

Research/candidate/untested records remain excluded from both gates.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import yaml

TARGETS = ("mihomo", "shadowrocket", "sing-box")


def load_yaml(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_modules(root: Path) -> list[dict]:
    modules = []
    for path in sorted(list(root.rglob("*.yaml")) + list(root.rglob("*.yml"))):
        doc = load_yaml(path)
        if isinstance(doc, dict) and "module" in doc and "rules" in doc:
            doc["_path"] = str(path)
            modules.append(doc)
    return modules


def publishable(module: dict, rule: dict, channel: str = "stable") -> bool:
    """Return whether a canonical matcher may cross the public boundary.

    RC publication proves routing identification, not complete service/account behavior.
    It requires corroborated-or-better evidence plus at least one successful runtime
    validation test. Stable publication additionally requires validation=passed and
    every test declared by the module release policy.
    """
    if channel not in {"rc", "stable"}:
        raise ValueError(f"unknown release channel: {channel}")
    policy = module.get("release_policy", {})
    rank = {"candidate": 0, "corroborated": 1, "verified": 2}
    evidence = rule.get("evidence", {}).get("level", "candidate")
    validation = rule.get("validation", {})
    state = validation.get("state", "untested")
    completed_tests = set(validation.get("tests", []))
    required_tests = set(policy.get("required_tests", []))
    ownership = rule.get("ownership")
    allowed = policy.get("allowed_ownership", [])
    conflicts = rule.get("conflicts", [])
    conflicts_ok = not policy.get("forbid_unresolved_policy_conflicts", False) or not conflicts
    ownership_ok = not allowed or ownership in allowed

    if channel == "rc":
        return (
            rank.get(evidence, -1) >= rank["corroborated"]
            and state in {"partial", "passed"}
            and bool(completed_tests)
            and ownership_ok
            and conflicts_ok
        )

    minimum = policy.get("minimum_evidence", "verified")
    return (
        rank.get(evidence, -1) >= rank.get(minimum, 2)
        and state == "passed"
        and required_tests.issubset(completed_tests)
        and ownership_ok
        and conflicts_ok
    )


def resolve_policy(module_id: str, policy_doc: dict) -> tuple[str, dict]:
    bindings = policy_doc["module_bindings"]
    logical = policy_doc["logical_policies"]
    if module_id not in bindings:
        raise ValueError(f"module has no policy binding: {module_id}")
    policy_id = bindings[module_id]
    if policy_id not in logical:
        raise ValueError(f"unknown logical policy: {module_id} -> {policy_id}")
    item = logical[policy_id]
    seen = {policy_id}
    while item.get("inherit_user_choice_from"):
        parent = item["inherit_user_choice_from"]
        if parent in seen:
            raise ValueError(f"policy inheritance cycle: {policy_id} -> {parent}")
        seen.add(parent)
        if parent not in logical:
            raise ValueError(f"unknown inherited policy: {policy_id} -> {parent}")
        item = logical[parent]
    return policy_id, item


def target_name(module_id: str, policy_doc: dict) -> str:
    _, resolved = resolve_policy(module_id, policy_doc)
    return resolved["display_name"]


def mihomo_line(rule: dict, group: str) -> str:
    m = rule["match"]
    mapping = {"domain":"DOMAIN","domain_suffix":"DOMAIN-SUFFIX","domain_keyword":"DOMAIN-KEYWORD","ip_cidr":"IP-CIDR","ip_cidr6":"IP-CIDR6","process_name":"PROCESS-NAME","process_path":"PROCESS-PATH"}
    if m["type"] not in mapping:
        raise ValueError(f"unsupported Mihomo matcher: {m['type']}")
    return f"{mapping[m['type']]},{m['value']},{group}"


def shadowrocket_line(rule: dict, group: str) -> str:
    m = rule["match"]
    mapping = {"domain":"DOMAIN","domain_suffix":"DOMAIN-SUFFIX","domain_keyword":"DOMAIN-KEYWORD","ip_cidr":"IP-CIDR","ip_cidr6":"IP-CIDR6","process_name":"PROCESS-NAME"}
    if m["type"] not in mapping:
        raise ValueError(f"unsupported Shadowrocket matcher: {m['type']}")
    return f"{mapping[m['type']]},{m['value']},{group}"


def singbox_rule(rule: dict, outbound: str) -> dict:
    m = rule["match"]
    mapping = {"domain":"domain","domain_suffix":"domain_suffix","domain_keyword":"domain_keyword","ip_cidr":"ip_cidr","ip_cidr6":"ip_cidr","process_name":"process_name","process_path":"process_path"}
    if m["type"] not in mapping:
        raise ValueError(f"unsupported sing-box matcher: {m['type']}")
    action = "direct" if outbound == "DIRECT" else "block" if outbound == "REJECT" else outbound
    return {mapping[m["type"]]: [m["value"]], "outbound": action}


def compile_module(module: dict, target: str, include_research: bool, policy_doc: dict, channel: str = "stable") -> str:
    module_id = module["module"]["id"]
    destination = target_name(module_id, policy_doc)
    selected = [r for r in module["rules"] if include_research or publishable(module, r, channel)]
    if target == "mihomo":
        return "\n".join(mihomo_line(r, destination) for r in selected) + ("\n" if selected else "")
    if target == "shadowrocket":
        return "\n".join(shadowrocket_line(r, destination) for r in selected) + ("\n" if selected else "")
    if target == "sing-box":
        return json.dumps({"version":1,"rules":[singbox_rule(r, destination) for r in selected]}, ensure_ascii=False, indent=2) + "\n"
    raise ValueError(target)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rules", default="rules")
    parser.add_argument("--policy", default="policies/v0.1.yaml")
    parser.add_argument("--out", default="build/proof")
    parser.add_argument("--include-research", action="store_true")
    parser.add_argument("--channel", choices=["rc", "stable"], default="stable")
    parser.add_argument("--target", choices=["all", *TARGETS], default="all")
    args = parser.parse_args()
    policy_doc = load_yaml(Path(args.policy))
    targets = TARGETS if args.target == "all" else (args.target,)
    modules = load_modules(Path(args.rules))
    out_root = Path(args.out)
    count = 0
    for module in modules:
        module_id = module["module"]["id"]
        for target in targets:
            ext = "json" if target == "sing-box" else "list"
            path = out_root / target / f"{module_id}.{ext}"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(compile_module(module, target, args.include_research, policy_doc, args.channel), encoding="utf-8")
            print(f"WROTE {path}")
            count += 1
    print(f"Generated {count} artifact(s) from {len(modules)} module(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
