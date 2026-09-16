#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import yaml

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "adapters" / "metacubex_geosite.py"
spec = importlib.util.spec_from_file_location("metacubex_geosite", PATH)
adapter = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(adapter)


def check(name, condition):
    if not condition:
        raise AssertionError(name)
    print(f"PASS {name}")


def main():
    doc = adapter.load_yaml_source(str(ROOT / "tests/fixtures/metacubex-geosite-sample.yaml"))
    payload = adapter.normalize_payload(doc)
    check("lowercase normalization", "+.youtube.com" in payload)
    check("suffix preserved", "+.googlevideo.com" in payload)
    check("exact domain preserved", "yt3.googleusercontent.com" in payload)
    check("duplicates removed", payload.count("+.youtube.com") == 1)

    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "provider.yaml"
        adapter.write_provider(payload, out)
        parsed = yaml.safe_load(out.read_text(encoding="utf-8"))
        check("provider shape", list(parsed) == ["payload"] and parsed["payload"] == payload)

    for bad in ["https://example.com", "example.com/path", "DOMAIN-SUFFIX,example.com", " bad domain.com "]:
        try:
            adapter.normalize_entry(bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid entry accepted: {bad}")
    print("PASS invalid entries fail closed")
    print("All MetaCubeX adapter tests passed")


if __name__ == "__main__":
    main()
