#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.normalize_hosts import normalize

def check(name, condition):
    if not condition:
        raise AssertionError(name)
    print("PASS", name)

def main():
    lines = [
        "# comment",
        "127.0.0.1 localhost",
        "0.0.0.0 ads.example.com",
        "127.0.0.1 tracker.example.net # inline",
        "0.0.0.0 a.example.org b.example.org",
        "8.8.8.8 not-a-block.example",
        "garbage",
    ]
    accepted, rejected = normalize(lines)
    by = {(x["type"], x["value"]): x for x in accepted}
    check("hosts entries lower to exact domain", ("domain", "ads.example.com") in by)
    check("hosts exact lowering recorded", by[("domain", "ads.example.com")]["semantic_lowering"] == "EXACT")
    check("multiple hostnames accepted", ("domain", "a.example.org") in by and ("domain", "b.example.org") in by)
    check("localhost ignored", all(x["value"] != "localhost" for x in accepted))
    check("non-block redirect rejected", any(x["reason"] == "non_block_redirect" for x in rejected))
    check("malformed line rejected", any(x["reason"] == "invalid_hosts_line" for x in rejected))
    print("All hosts normalizer tests passed")

if __name__ == "__main__":
    main()
