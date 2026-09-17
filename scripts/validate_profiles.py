#!/usr/bin/env python3
"""Validate Hrules user-facing scenario profiles against canonical modules.

Profiles are scenario manifests only. They must not duplicate canonical rule facts.
This validator guarantees that inheritance is acyclic, referenced modules exist,
and client declarations use the small supported status vocabulary.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import yaml


def load(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def canonical_modules(root: Path) -> set[str]:
    result: set[str] = set()
    for path in sorted(list(root.rglob("*.yaml")) + list(root.rglob("*.yml"))):
        doc = load(path)
        if isinstance(doc, dict) and isinstance(doc.get("module"), dict) and doc["module"].get("id"):
            result.add(doc["module"]["id"])
    return result


def resolve_profile(name: str, profiles: dict, modules: set[str], stack: tuple[str, ...] = ()) -> list[str]:
    if name not in profiles:
        raise ValueError(f"unknown profile: {name}")
    if name in stack:
        chain = " -> ".join((*stack, name))
        raise ValueError(f"profile inheritance cycle: {chain}")
    item = profiles[name]
    if item.get("include_all"):
        return sorted(modules)

    resolved: list[str] = []
    for parent in item.get("extends", []) or []:
        for module_id in resolve_profile(parent, profiles, modules, (*stack, name)):
            if module_id not in resolved:
                resolved.append(module_id)
    for module_id in item.get("include", []) or []:
        if module_id not in modules:
            raise ValueError(f"profile {name} references unknown module: {module_id}")
        if module_id not in resolved:
            resolved.append(module_id)
    return resolved


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profiles", default="profiles/v0.1.yaml")
    parser.add_argument("--rules", default="rules")
    args = parser.parse_args()

    doc = load(Path(args.profiles))
    profiles = doc.get("profiles", {})
    clients = doc.get("clients", {})
    modules = canonical_modules(Path(args.rules))
    failures = 0

    if not profiles:
        print("FAIL no profiles declared")
        failures += 1

    for name, item in profiles.items():
        if item.get("include_all") and (item.get("include") or item.get("extends")):
            print(f"FAIL {name}: include_all cannot be combined with include/extends")
            failures += 1
        try:
            resolved = resolve_profile(name, profiles, modules)
        except ValueError as exc:
            print(f"FAIL {exc}")
            failures += 1
            continue
        if not resolved:
            print(f"FAIL {name}: resolves to zero modules")
            failures += 1
            continue
        print(f"PROFILE {name}: {len(resolved)} module(s) -> {', '.join(resolved)}")

    allowed_client_status = {"planned", "validating", "public", "deprecated"}
    for client_id, item in clients.items():
        status = item.get("status")
        names = item.get("public_names") or []
        if status not in allowed_client_status:
            print(f"FAIL client {client_id}: invalid status {status!r}")
            failures += 1
        if not names or any(not isinstance(name, str) or not name.strip() for name in names):
            print(f"FAIL client {client_id}: public_names must be non-empty strings")
            failures += 1

    print(f"Validated {len(profiles)} profiles, {len(clients)} client declarations and {len(modules)} canonical modules; failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
