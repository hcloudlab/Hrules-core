#!/usr/bin/env python3
"""Build the public Hrules release tree from publishable canonical records only.

This publisher is deliberately fail-closed:
- research/candidate/partial records never cross the public boundary;
- a module is emitted only when compile_rules.publishable() selects records;
- an empty release is rejected;
- generated files include a SHA256 manifest for auditability.

It writes a staging directory only. Publishing that directory to hcloudlab/Hrules is a
separate action after CI validates the staged release.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import yaml

ROOT = Path(__file__).resolve().parents[1]
COMPILER_PATH = ROOT / "generators" / "compile_rules.py"
spec = importlib.util.spec_from_file_location("compile_rules", COMPILER_PATH)
compiler = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(compiler)


def load_yaml(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--rules", default="rules")
    p.add_argument("--policy", default="policies/v0.1.yaml")
    p.add_argument("--release-manifest", default="manifests/v0.1-release-candidate.yaml")
    p.add_argument("--out", default="build/public-release")
    p.add_argument("--allow-empty", action="store_true", help="CI/testing only; never use for a public release")
    args = p.parse_args()

    manifest = load_yaml(Path(args.release_manifest))
    version = manifest["release"]["version"]
    policy = load_yaml(Path(args.policy))
    modules = compiler.load_modules(Path(args.rules))
    out = Path(args.out)
    if out.exists():
        shutil.rmtree(out)
    (out / "mihomo").mkdir(parents=True, exist_ok=True)

    emitted: list[dict] = []
    skipped: list[str] = []
    for module in modules:
        module_id = module["module"]["id"]
        text = compiler.compile_module(module, "mihomo", False, policy)
        if not text.strip():
            skipped.append(module_id)
            continue
        path = out / "mihomo" / f"{module_id}.list"
        path.write_text(text, encoding="utf-8")
        emitted.append({"path": str(path.relative_to(out)), "sha256": sha256(path), "module": module_id})

    if not emitted and not args.allow_empty:
        raise SystemExit(
            "REFUSED: no canonical records satisfy public release policy. "
            "Do not use --include-research for publication; promote evidence/validation first."
        )

    public_manifest = {
        "schema_version": 1,
        "version": version,
        "source": manifest["release"]["source_repository"],
        "artifacts": emitted,
        "skipped_non_publishable_modules": sorted(skipped),
    }
    manifest_path = out / "manifest.json"
    manifest_path.write_text(json.dumps(public_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    sums = [f"{item['sha256']}  {item['path']}" for item in emitted]
    sums.append(f"{sha256(manifest_path)}  manifest.json")
    (out / "SHA256SUMS").write_text("\n".join(sums) + "\n", encoding="utf-8")

    print(f"STAGED {len(emitted)} public artifact(s); skipped {len(skipped)} non-publishable module(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
