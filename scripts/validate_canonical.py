#!/usr/bin/env python3
"""Validate Hrules canonical YAML modules against the v0.1 JSON Schema.

Requires: PyYAML, jsonschema
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, FormatChecker


def load_yaml(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def collect_yaml(paths: list[str]) -> list[Path]:
    result: list[Path] = []
    for raw in paths:
        path = Path(raw)
        if path.is_dir():
            result.extend(sorted(path.rglob("*.yaml")))
            result.extend(sorted(path.rglob("*.yml")))
        else:
            result.append(path)
    return sorted(set(result))


def format_path(parts) -> str:
    return ".".join(str(p) for p in parts) or "<root>"


def semantic_checks(doc: dict, path: Path) -> list[str]:
    errors: list[str] = []
    seen_ids: set[str] = set()
    seen_matches: dict[tuple[str, str], str] = {}

    for rule in doc.get("rules", []):
        rule_id = rule.get("id", "<missing-id>")
        if rule_id in seen_ids:
            errors.append(f"{path}: duplicate rule id: {rule_id}")
        seen_ids.add(rule_id)

        match = rule.get("match", {})
        match_type = match.get("type")
        value = match.get("value")
        if isinstance(value, str):
            if match_type in {"domain", "domain_suffix"}:
                if value != value.lower():
                    errors.append(f"{path}: {rule_id}: domain must be lowercase: {value}")
                if "://" in value or "/" in value:
                    errors.append(f"{path}: {rule_id}: domain must not contain scheme/path: {value}")
                if value.startswith(".") or value.endswith("."):
                    errors.append(f"{path}: {rule_id}: domain must not start/end with dot: {value}")

            key = (str(match_type), value)
            previous = seen_matches.get(key)
            if previous:
                errors.append(
                    f"{path}: duplicate matcher {match_type}:{value} in {previous} and {rule_id}"
                )
            else:
                seen_matches[key] = rule_id

        validation = rule.get("validation", {})
        evidence = rule.get("evidence", {})
        if validation.get("state") == "passed" and not validation.get("tests"):
            errors.append(f"{path}: {rule_id}: passed validation requires at least one test")
        if evidence.get("level") == "verified" and validation.get("state") not in {"passed", "stale"}:
            errors.append(
                f"{path}: {rule_id}: verified evidence requires passed/stale runtime validation"
            )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "paths",
        nargs="*",
        default=["rules"],
        help="YAML files or directories (default: rules)",
    )
    parser.add_argument(
        "--schema",
        default="schemas/canonical-rule.schema.json",
        help="Canonical JSON Schema path",
    )
    args = parser.parse_args()

    schema_path = Path(args.schema)
    schema = load_json(schema_path)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())

    files = collect_yaml(args.paths)
    if not files:
        print("ERROR: no YAML modules found", file=sys.stderr)
        return 2

    failures = 0
    for path in files:
        try:
            doc = load_yaml(path)
        except Exception as exc:
            print(f"FAIL {path}: YAML parse error: {exc}")
            failures += 1
            continue

        schema_errors = sorted(validator.iter_errors(doc), key=lambda e: list(e.absolute_path))
        semantic_errors = semantic_checks(doc if isinstance(doc, dict) else {}, path)

        if schema_errors or semantic_errors:
            failures += 1
            print(f"FAIL {path}")
            for err in schema_errors:
                print(f"  schema {format_path(err.absolute_path)}: {err.message}")
            for err in semantic_errors:
                print(f"  semantic: {err}")
        else:
            print(f"PASS {path}")

    print(f"Validated {len(files)} module(s); failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
