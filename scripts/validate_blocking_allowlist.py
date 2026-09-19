#!/usr/bin/env python3
"""Validate the Blocking allowlist schema and semantic constraints."""
from __future__ import annotations
import json, sys
from datetime import date
from pathlib import Path
import yaml
from jsonschema import Draft202012Validator, FormatChecker

def main()->int:
    path=Path("sources/blocking-allowlist.yaml")
    schema=json.loads(Path("schemas/blocking-allowlist.schema.json").read_text())
    doc=yaml.safe_load(path.read_text()) or {}
    errors=list(Draft202012Validator(schema,format_checker=FormatChecker()).iter_errors(doc))
    seen=set()
    for item in doc.get("entries",[]):
        m=item["match"]; key=(m["type"],m["value"].lower())
        if m["value"] != m["value"].lower(): errors.append(ValueError(f"allowlist domain must be lowercase: {m['value']}"))
        if key in seen: errors.append(ValueError(f"duplicate allowlist matcher: {key[0]}:{key[1]}"))
        seen.add(key)
        if item.get("expires") and date.fromisoformat(item["expires"]) < date.today():
            errors.append(ValueError(f"expired allowlist entry: {key[0]}:{key[1]}"))
    if errors:
        for e in errors: print("FAIL", getattr(e,"message",str(e)))
        return 1
    print(f"PASS Blocking allowlist entries={len(doc.get('entries',[]))}")
    return 0
if __name__=="__main__": raise SystemExit(main())
