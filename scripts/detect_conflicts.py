#!/usr/bin/env python3
"""Detect cross-module canonical matcher conflicts.

v0.1 detects exact duplicate matchers and domain/domain-suffix containment overlaps.
It reports policy conflicts when overlapping modules have different policy classes.
"""
from __future__ import annotations

import argparse
import ipaddress
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

from generators import compile_rules as compiler


@dataclass(frozen=True)
class Entry:
    module: str
    policy: str
    rule_id: str
    match_type: str
    value: str
    path: Path


def load_entries(root: Path) -> list[Entry]:
    entries: list[Entry] = []
    for path in sorted(list(root.rglob("*.yaml")) + list(root.rglob("*.yml"))):
        with path.open("r", encoding="utf-8") as fh:
            doc = yaml.safe_load(fh)
        if not isinstance(doc, dict):
            continue
        module = doc.get("module", {})
        module_id = module.get("id", "<unknown>")
        policy = module.get("policy_class", "<unknown>")
        for rule in doc.get("rules", []):
            match = rule.get("match", {})
            entries.append(Entry(module_id, policy, rule.get("id", "<unknown>"), match.get("type", ""), str(match.get("value", "")), path))
    return entries


def domain_overlap(a: Entry, b: Entry) -> bool:
    domain_types = {"domain", "domain_suffix"}
    if a.match_type not in domain_types or b.match_type not in domain_types:
        return False
    av, bv = a.value.lower(), b.value.lower()
    if av == bv:
        return True
    if a.match_type == "domain_suffix" and (bv == av or bv.endswith("." + av)):
        return True
    if b.match_type == "domain_suffix" and (av == bv or av.endswith("." + bv)):
        return True
    return False


def ip_overlap(a: Entry, b: Entry) -> bool:
    if a.match_type not in {"ip_cidr", "ip_cidr6"} or b.match_type not in {"ip_cidr", "ip_cidr6"}:
        return False
    try:
        an = ipaddress.ip_network(a.value, strict=False)
        bn = ipaddress.ip_network(b.value, strict=False)
    except ValueError:
        return False
    return an.version == bn.version and an.overlaps(bn)


def relation(a: Entry, b: Entry) -> str | None:
    if a.match_type == b.match_type and a.value == b.value:
        return "duplicate"
    if domain_overlap(a, b) or ip_overlap(a, b):
        return "overlap"
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default="rules")
    args = parser.parse_args()
    entries = load_entries(Path(args.root))

    warnings = 0
    blockers = 0
    for i, a in enumerate(entries):
        for b in entries[i + 1:]:
            if a.module == b.module:
                continue
            rel = relation(a, b)
            if not rel:
                continue
            policy_conflict = a.policy != b.policy
            level = "BLOCK" if policy_conflict else "WARN"
            if policy_conflict:
                blockers += 1
            else:
                warnings += 1
            print(f"{level} {rel}: {a.module}/{a.rule_id} [{a.policy}] <-> {b.module}/{b.rule_id} [{b.policy}]")

    print(f"Scanned {len(entries)} rule(s); warnings={warnings}; blockers={blockers}")
    return 1 if blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
