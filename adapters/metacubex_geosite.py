#!/usr/bin/env python3
"""Normalize MetaCubeX geosite YAML into an Hrules Mihomo domain provider payload."""
from __future__ import annotations

import argparse
from pathlib import Path
from urllib.request import urlopen
import yaml


def load_yaml_source(source: str):
    if source.startswith("https://"):
        with urlopen(source, timeout=30) as resp:
            return yaml.safe_load(resp.read().decode("utf-8"))
    with Path(source).open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def normalize_entry(raw: str) -> str:
    if not isinstance(raw, str):
        raise ValueError(f"provider entry must be string, got {type(raw).__name__}")
    value = raw.strip().lower()
    if not value:
        raise ValueError("provider entry must not be empty")
    if "://" in value or "/" in value or "," in value or " " in value:
        raise ValueError(f"unsupported domain-provider entry: {raw!r}")
    if value.startswith("+."):
        domain = value[2:]
        if not domain or domain.startswith(".") or domain.endswith("."):
            raise ValueError(f"invalid suffix entry: {raw!r}")
        return "+." + domain
    if value.startswith(".") or value.endswith("."):
        raise ValueError(f"invalid exact-domain entry: {raw!r}")
    return value


def normalize_payload(doc: dict) -> list[str]:
    if not isinstance(doc, dict) or not isinstance(doc.get("payload"), list):
        raise ValueError("upstream document must contain a payload list")
    seen: set[str] = set()
    result: list[str] = []
    for raw in doc["payload"]:
        value = normalize_entry(raw)
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    if not result:
        raise ValueError("normalized payload is empty")
    return result


def write_provider(payload: list[str], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(yaml.safe_dump({"payload": payload}, allow_unicode=True, sort_keys=False), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", help="local YAML path or HTTPS URL")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    payload = normalize_payload(load_yaml_source(args.source))
    out = Path(args.out)
    write_provider(payload, out)
    print(f"WROTE {out}: entries={len(payload)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
