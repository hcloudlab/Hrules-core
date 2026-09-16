#!/usr/bin/env python3
"""Small proof tests for canonical semantic rules.

Run with: python3 tests/test_canonical_validator.py
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "scripts" / "validate_canonical.py"

spec = importlib.util.spec_from_file_location("validate_canonical", VALIDATOR_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)
semantic_checks = module.semantic_checks


def base_rule(rule_id: str, value: str) -> dict:
    return {
        "id": rule_id,
        "match": {"type": "domain_suffix", "value": value},
        "ownership": "first_party",
        "purpose": "service_core",
        "provenance": {"kind": "first_party", "source": "official_service"},
        "evidence": {"level": "candidate", "methods": ["official_domain"]},
        "validation": {"state": "untested", "tests": []},
        "conflicts": [],
    }


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS {name}")


def main() -> None:
    fixture = Path("fixture.yaml")

    valid = {"rules": [base_rule("claude.domain.claude-ai", "claude.ai")]}
    check("valid candidate", semantic_checks(valid, fixture) == [])

    uppercase = {"rules": [base_rule("x", "Claude.AI")]}
    check("reject uppercase domain", any("lowercase" in e for e in semantic_checks(uppercase, fixture)))

    url_value = {"rules": [base_rule("x", "https://claude.ai/login")]}
    check("reject URL as domain", any("scheme/path" in e for e in semantic_checks(url_value, fixture)))

    duplicate = {"rules": [base_rule("a", "claude.ai"), base_rule("b", "claude.ai")]}
    check("detect duplicate matcher", any("duplicate matcher" in e for e in semantic_checks(duplicate, fixture)))

    verified_unvalidated = base_rule("x", "claude.ai")
    verified_unvalidated["evidence"]["level"] = "verified"
    check(
        "verified requires runtime validation",
        any("verified evidence" in e for e in semantic_checks({"rules": [verified_unvalidated]}, fixture)),
    )

    passed_without_tests = base_rule("x", "claude.ai")
    passed_without_tests["validation"]["state"] = "passed"
    check(
        "passed requires tests",
        any("at least one test" in e for e in semantic_checks({"rules": [passed_without_tests]}, fixture)),
    )

    print("All canonical semantic proof tests passed")


if __name__ == "__main__":
    main()
