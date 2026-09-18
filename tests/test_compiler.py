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
        "routing_stages": {"private": 10, "ordinary_service": 40},
        "logical_policies": {
            "example_policy": {
                "display_name": "Example Group",
                "routing_stage": "ordinary_service",
                "behavior": "ordinary_proxy",
                "user_visible": True,
            },
            "private_direct": {
                "display_name": "DIRECT",
                "routing_stage": "private",
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

    private_for_order = module(module_id="private", match_type="ip_cidr", value="10.0.0.0/8")
    ordered = compiler.order_modules([research, private_for_order], policy)
    check("semantic routing stage beats input/path order", [m["module"]["id"] for m in ordered] == ["private", "example"])

    excluded = module()
    excluded["exclusions"] = [{"match": {"type": "domain_suffix", "value": "example.com"}, "reason": "test"}]
    check("exact exclusion suppresses matcher", compiler.compile_module(excluded, "mihomo", True, policy) == "")\n\n    ordered_exclusions = module(value="example.com")\n    ordered_exclusions["exclusions"] = [\n        {"match": {"type": "domain", "value": "login.example.com"}, "reason": "narrow"},\n        {"match": {"type": "domain_suffix", "value": "example.com"}, "reason": "broad suppressor"},\n    ]\n    check("suppression beats earlier subtractive exclusion", compiler.compile_module(ordered_exclusions, "mihomo", True, policy) == "")\n\n    keyword = module(match_type="domain_keyword", value="google")\n    keyword["exclusions"] = [{"match": {"type": "domain", "value": "login.google.com"}, "reason": "narrow"}]\n    try:\n        compiler.compile_module(keyword, "mihomo", True, policy)\n    except ValueError as exc:\n        check("keyword narrower exclusion fails closed", "subtractive lowering unsupported" in str(exc))\n    else:\n        raise AssertionError("keyword narrower exclusion must fail closed")

    subtractive = module(value="example.com")
    subtractive["exclusions"] = [{"match": {"type": "domain", "value": "login.example.com"}, "reason": "shared"}]
    try:
        compiler.compile_module(subtractive, "mihomo", True, policy)
    except ValueError as exc:
        check("narrow exclusion fails closed", "subtractive lowering unsupported" in str(exc))
    else:
        raise AssertionError("narrow exclusion must fail closed")

    check("Shadowrocket process_path declared unsupported", compiler.lowering_status("shadowrocket", "process_path") == "UNSUPPORTED")
    check("Mihomo domain suffix lowering exact", compiler.lowering_status("mihomo", "domain_suffix") == "EXACT")

    released = module(evidence="verified", state="passed")
    rule = released["rules"][0]
    check("verified passed record is publishable", compiler.publishable(released, rule))
    check("mihomo provider matcher is policy-free", compiler.mihomo_matcher(rule) == "DOMAIN-SUFFIX,example.com")
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
