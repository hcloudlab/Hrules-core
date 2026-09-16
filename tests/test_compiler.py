#!/usr/bin/env python3
"""Contract tests for the compiler prototype."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "generators" / "compile_rules.py"
spec = importlib.util.spec_from_file_location("compile_rules", PATH)
compiler = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(compiler)


def module(match_type="domain_suffix", value="example.com", evidence="candidate", state="untested"):
    return {
        "module": {"id": "example", "policy_class": "ordinary_proxy"},
        "release_policy": {"minimum_evidence": "verified", "allowed_ownership": ["first_party"]},
        "rules": [{
            "id": "example.rule",
            "match": {"type": match_type, "value": value},
            "ownership": "first_party",
            "evidence": {"level": evidence, "methods": []},
            "validation": {"state": state, "tests": []},
        }],
    }


def check(name, condition):
    if not condition:
        raise AssertionError(name)
    print(f"PASS {name}")


def main():
    research = module()
    check("research excluded from release build", compiler.compile_module(research, "mihomo", False) == "")
    check("research can be proof-compiled", "DOMAIN-SUFFIX,example.com,HRULES::example" in compiler.compile_module(research, "mihomo", True))

    released = module(evidence="verified", state="passed")
    check("verified passed record is publishable", compiler.publishable(released, released["rules"][0]))
    check("mihomo lowering", compiler.compile_module(released, "mihomo", False).startswith("DOMAIN-SUFFIX,example.com"))
    check("shadowrocket lowering", compiler.compile_module(released, "shadowrocket", False).startswith("DOMAIN-SUFFIX,example.com"))
    sb = compiler.compile_module(released, "sing-box", False)
    check("sing-box lowering", '"domain_suffix"' in sb and '"example.com"' in sb)

    unsupported = module(match_type="process_path")
    try:
        compiler.compile_module(unsupported, "shadowrocket", True)
    except ValueError:
        pass
    else:
        raise AssertionError("unsupported matcher must fail closed")
    print("PASS unsupported matcher fails closed")

    print("All compiler contract tests passed")


if __name__ == "__main__":
    main()
