#!/usr/bin/env python3
"""Contract tests for the policy-aware compiler prototype."""
from __future__ import annotations
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "generators" / "compile_rules.py"
spec = importlib.util.spec_from_file_location("compile_rules", PATH)
compiler = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(compiler)


def policy_doc():
    return {
        "logical_policies": {
            "example_policy": {
                "display_name": "Example Group",
                "behavior": "ordinary_proxy",
                "user_visible": True,
            },
            "private_direct": {
                "display_name": "DIRECT",
                "behavior": "direct_preferred",
                "user_visible": False,
            },
        },
        "module_bindings": {"example": "example_policy", "private": "private_direct"},
    }


def module(module_id="example", match_type="domain_suffix", value="example.com", evidence="candidate", state="untested"):
    return {
        "module": {"id": module_id, "policy_class": "ordinary_proxy"},
        "release_policy": {"minimum_evidence": "verified", "allowed_ownership": ["first_party"]},
        "rules": [{
            "id": f"{module_id}.rule",
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
    policy = policy_doc()
    research = module()
    check("research excluded from release build", compiler.compile_module(research, "mihomo", False, policy) == "")
    proof = compiler.compile_module(research, "mihomo", True, policy)
    check("research can be proof-compiled", "DOMAIN-SUFFIX,example.com,Example Group" in proof)
    check("temporary HRULES namespace removed", "HRULES::" not in proof)

    released = module(evidence="verified", state="passed")
    check("verified passed record is publishable", compiler.publishable(released, released["rules"][0]))
    check("mihomo policy lowering", compiler.compile_module(released, "mihomo", False, policy).startswith("DOMAIN-SUFFIX,example.com,Example Group"))
    check("shadowrocket policy lowering", compiler.compile_module(released, "shadowrocket", False, policy).startswith("DOMAIN-SUFFIX,example.com,Example Group"))
    sb = compiler.compile_module(released, "sing-box", False, policy)
    check("sing-box policy lowering", '"domain_suffix"' in sb and '"Example Group"' in sb)

    private = module(module_id="private", match_type="ip_cidr", value="10.0.0.0/8", evidence="verified", state="passed")
    check("Mihomo DIRECT terminal", compiler.compile_module(private, "mihomo", False, policy).strip().endswith(",DIRECT"))
    check("sing-box DIRECT terminal", '"outbound": "direct"' in compiler.compile_module(private, "sing-box", False, policy))

    unsupported = module(match_type="process_path")
    try:
        compiler.compile_module(unsupported, "shadowrocket", True, policy)
    except ValueError:
        pass
    else:
        raise AssertionError("unsupported matcher must fail closed")
    print("PASS unsupported matcher fails closed")

    unknown = module(module_id="unbound")
    try:
        compiler.compile_module(unknown, "mihomo", True, policy)
    except ValueError:
        pass
    else:
        raise AssertionError("unbound module must fail closed")
    print("PASS unbound module fails closed")

    print("All compiler contract tests passed")


if __name__ == "__main__":
    main()
