#!/usr/bin/env python3
"""Strict hosts-file normalizer. Host redirects map to exact canonical domain matchers."""
from __future__ import annotations
import argparse, ipaddress, json, re
from pathlib import Path

DOMAIN = re.compile(r"^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")
BLOCK_IPS = {"0.0.0.0", "127.0.0.1", "::", "::1"}
IGNORED_HOSTS = {"localhost", "localhost.localdomain", "broadcasthost", "ip6-localhost", "ip6-loopback"}

def classify(line: str):
    raw = line.strip()
    if not raw or raw.startswith("#"):
        return ("ignore", [], "comment_or_blank")
    raw = raw.split("#", 1)[0].strip()
    parts = raw.split()
    if len(parts) < 2:
        return ("reject", [], "invalid_hosts_line")
    try:
        ipaddress.ip_address(parts[0])
    except ValueError:
        return ("reject", [], "invalid_ip")
    if parts[0] not in BLOCK_IPS:
        return ("reject", [], "non_block_redirect")
    accepted = []
    rejected = []
    for token in parts[1:]:
        value = token.lower().rstrip(".")
        if value in IGNORED_HOSTS:
            continue
        if DOMAIN.fullmatch(value):
            accepted.append({"type": "domain", "value": value, "source_syntax": "hosts_redirect", "semantic_lowering": "EXACT"})
        else:
            rejected.append(value)
    if rejected:
        return ("partial" if accepted else "reject", accepted, "invalid_hostname")
    return ("accept" if accepted else "ignore", accepted, "localhost_or_empty")

def normalize(lines):
    accepted, rejected, seen = [], [], set()
    for n, line in enumerate(lines, 1):
        state, matches, reason = classify(line)
        for match in matches:
            key = (match["type"], match["value"])
            if key not in seen:
                accepted.append(match)
                seen.add(key)
        if state in {"reject", "partial"}:
            rejected.append({"line": n, "reason": reason, "input": line.rstrip("\n")})
    return accepted, rejected

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("input")
    p.add_argument("--out", required=True)
    p.add_argument("--rejects", required=True)
    p.add_argument("--max-reject-ratio", type=float, default=.01)
    a = p.parse_args()
    accepted, rejected = normalize(Path(a.input).read_text(encoding="utf-8", errors="replace").splitlines())
    classified = len(accepted) + len(rejected)
    ratio = len(rejected) / classified if classified else 1
    Path(a.rejects).write_text(json.dumps(rejected, ensure_ascii=False, indent=2) + "\n")
    if not accepted or ratio > a.max_reject_ratio:
        print(f"REFUSED hosts normalization: accepted={len(accepted)} rejected={len(rejected)} ratio={ratio:.3f}")
        return 1
    Path(a.out).write_text(json.dumps({"matches": accepted}, ensure_ascii=False, indent=2) + "\n")
    print(f"NORMALIZED hosts accepted={len(accepted)} rejected={len(rejected)} ratio={ratio:.3f}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
