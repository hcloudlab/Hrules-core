#!/usr/bin/env python3
"""Validate logical policy mapping and its references to canonical modules."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
import yaml
from jsonschema import Draft202012Validator


def load(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def canonical_modules(root: Path) -> dict[str, str]:
    result = {}
    for path in sorted(list(root.rglob("*.yaml")) + list(root.rglob("*.yml"))):
        doc = load(path)
        if not isinstance(doc, dict) or "module" not in doc:
            continue
        module = doc["module"]
        result[module["id"]] = module["policy_class"]
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", default="policies/v0.1.yaml")
    parser.add_argument("--schema", default="schemas/policy.schema.json")
    parser.add_argument("--rules", default="rules")
    args = parser.parse_args()

    policy = load(Path(args.policy))
    schema = json.loads(Path(args.schema).read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(policy), key=lambda e: list(e.absolute_path))
    for error in errors:
        print(f"SCHEMA FAIL {'.'.join(map(str, error.absolute_path)) or '<root>'}: {error.message}")
    if errors:
        return 1

    modules = canonical_modules(Path(args.rules))
    logical = policy["logical_policies"]
    bindings = policy["module_bindings"]
    failures = 0

    for module_id, target in bindings.items():
        if module_id not in modules:
            print(f"FAIL binding references unknown module: {module_id}")
            failures += 1
        if target not in logical:
            print(f"FAIL binding references unknown logical policy: {module_id} -> {target}")
            failures += 1

    for policy_id, item in logical.items():
        parent = item.get("inherit_user_choice_from")
        if parent and parent not in logical:
            print(f"FAIL {policy_id} inherits unknown policy: {parent}")
            failures += 1
        if parent and parent == policy_id:
            print(f"FAIL {policy_id} cannot inherit from itself")
            failures += 1

    # Every current proof module must have an explicit binding. This prevents
    # compiler fallback from silently sending new services to a default policy.
    for module_id in modules:
        if module_id not in bindings:
            print(f"FAIL canonical module has no policy binding: {module_id}")
            failures += 1

    print(f"Validated {len(logical)} logical policies and {len(bindings)} module bindings; failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
