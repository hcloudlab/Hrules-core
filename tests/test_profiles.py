#!/usr/bin/env python3
"""Contract tests for Hrules multi-scenario profile resolution."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts" / "validate_profiles.py"
spec = importlib.util.spec_from_file_location("validate_profiles", PATH)
profiles_mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(profiles_mod)


def check(name, condition):
    if not condition:
        raise AssertionError(name)
    print(f"PASS {name}")


def main():
    modules = {"private", "cn", "youtube", "claude", "openai", "binance"}
    profiles = {
        "basic": {"include": ["private", "cn", "youtube"]},
        "ai": {"extends": ["basic"], "include": ["claude", "openai"]},
        "crypto": {"extends": ["ai"], "include": ["binance"]},
        "full": {"include_all": True},
    }

    check("basic resolves direct modules", profiles_mod.resolve_profile("basic", profiles, modules) == ["private", "cn", "youtube"])
    check("ai inherits basic", profiles_mod.resolve_profile("ai", profiles, modules) == ["private", "cn", "youtube", "claude", "openai"])
    check("crypto inherits ai transitively", profiles_mod.resolve_profile("crypto", profiles, modules)[-1] == "binance")
    check("full resolves all canonical modules", profiles_mod.resolve_profile("full", profiles, modules) == sorted(modules))

    duplicate = {
        "base": {"include": ["private"]},
        "child": {"extends": ["base"], "include": ["private", "cn"]},
    }
    check("inheritance deduplicates modules", profiles_mod.resolve_profile("child", duplicate, modules) == ["private", "cn"])

    try:
        profiles_mod.resolve_profile("bad", {"bad": {"include": ["missing"]}}, modules)
    except ValueError:
        pass
    else:
        raise AssertionError("unknown module must fail closed")
    print("PASS unknown module fails closed")

    cyclic = {"a": {"extends": ["b"]}, "b": {"extends": ["a"]}}
    try:
        profiles_mod.resolve_profile("a", cyclic, modules)
    except ValueError:
        pass
    else:
        raise AssertionError("profile cycle must fail closed")
    print("PASS profile cycle fails closed")

    print("All profile contract tests passed")


if __name__ == "__main__":
    main()
