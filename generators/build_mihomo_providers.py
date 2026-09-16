#!/usr/bin/env python3
"""Build pinned Hrules Mihomo domain-provider artifacts from approved upstream adapters."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
ADAPTER_PATH = ROOT / "adapters" / "metacubex_geosite.py"
spec = importlib.util.spec_from_file_location("metacubex_geosite", ADAPTER_PATH)
adapter = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(adapter)


def load(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def raw_url(repo: str, commit: str, path: str) -> str:
    return f"https://raw.githubusercontent.com/{repo}/{commit}/{path}"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", default="sources/adapters/metacubex-geosite.yaml")
    p.add_argument("--out", default="build/providers/mihomo")
    p.add_argument("--only", default="", help="comma-separated provider ids")
    args = p.parse_args()

    manifest = load(Path(args.manifest))
    source = manifest["source"]
    wanted = {x for x in args.only.split(",") if x}
    out_root = Path(args.out)
    out_root.mkdir(parents=True, exist_ok=True)
    built = []

    for provider_id, cfg in manifest["providers"].items():
        if wanted and provider_id not in wanted:
            continue
        url = raw_url(source["repository"], source["pinned_commit"], cfg["upstream_path"])
        payload = adapter.normalize_payload(adapter.load_yaml_source(url))
        missing = [probe for probe in cfg.get("required_probes", []) if probe not in payload]
        if missing:
            raise ValueError(f"{provider_id}: missing required probes: {missing}")
        path = out_root / f"{provider_id}.yaml"
        adapter.write_provider(payload, path)
        built.append({
            "id": provider_id,
            "behavior": cfg["behavior"],
            "target_policy": cfg["target_policy"],
            "entries": len(payload),
            "sha256": sha256(path),
            "source_repository": source["repository"],
            "source_commit": source["pinned_commit"],
            "source_path": cfg["upstream_path"],
            "license": source["license"],
        })
        print(f"WROTE {path}: entries={len(payload)}")

    if not built:
        raise ValueError("no providers selected")
    metadata = {"schema_version": 1, "providers": built}
    meta_path = out_root / "manifest.json"
    meta_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"WROTE {meta_path}: providers={len(built)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
