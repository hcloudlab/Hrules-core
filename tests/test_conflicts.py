#!/usr/bin/env python3
"""Regression tests for cross-module CIDR conflict detection."""
from __future__ import annotations
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts" / "detect_conflicts.py"
spec = importlib.util.spec_from_file_location("detect_conflicts", PATH)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

def entry(module, policy, rule_id, match_type, value):
    return mod.Entry(module, policy, rule_id, match_type, value, Path("fixture.yaml"))

def check(name, condition):
    if not condition:
        raise AssertionError(name)
    print(f"PASS {name}")

def main():
    a = entry("a", "direct_preferred", "a.net", "ip_cidr", "10.0.0.0/8")
    b = entry("b", "sensitive_account", "b.net", "ip_cidr", "10.1.0.0/16")
    c = entry("c", "sensitive_account", "c.net", "ip_cidr", "192.168.0.0/16")
    v6a = entry("v6a", "direct_preferred", "v6a.net", "ip_cidr6", "fc00::/7")
    v6b = entry("v6b", "ordinary_proxy", "v6b.net", "ip_cidr6", "fd00::/8")

    check("IPv4 containment overlap detected", mod.relation(a, b) == "overlap")
    check("disjoint IPv4 networks ignored", mod.relation(a, c) is None)
    check("IPv6 containment overlap detected", mod.relation(v6a, v6b) == "overlap")
    check("domain/IP families never overlap", mod.relation(a, entry("d","ordinary_proxy","d","domain_suffix","example.com")) is None)
    print("All conflict regression tests passed")

if __name__ == "__main__":
    main()
