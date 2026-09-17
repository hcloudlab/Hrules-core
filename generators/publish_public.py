#!/usr/bin/env python3
"""Build the public Hrules release tree from canonical records.

The release manifest determines the channel. v0.1.0-rc* uses the RC gate: only
corroborated-or-better matchers with successful runtime routing validation cross the
public boundary. Stable releases use the stricter stable gate and require every
module-declared test. Candidate/untested records never publish.
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
    h = hashlib.sha256(); h.update(path.read_bytes()); return h.hexdigest()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--rules", default="rules")
    p.add_argument("--policy", default="policies/v0.1.yaml")
    p.add_argument("--release-manifest", default="manifests/v0.1-release-candidate.yaml")
    p.add_argument("--out", default="build/public-release")
    p.add_argument("--allow-empty", action="store_true", help="CI/testing only")
    args = p.parse_args()

    manifest = load_yaml(Path(args.release_manifest))
    version = manifest["release"]["version"]
    channel = "rc" if "-rc" in version else "stable"
    policy = load_yaml(Path(args.policy))
    modules = compiler.load_modules(Path(args.rules))
    out = Path(args.out)
    if out.exists(): shutil.rmtree(out)
    (out / "mihomo").mkdir(parents=True, exist_ok=True)

    emitted, skipped = [], []
    for module in modules:
        module_id = module["module"]["id"]
        text = compiler.compile_module(module, "mihomo", False, policy, channel)
        if not text.strip():
            skipped.append(module_id); continue
        path = out / "mihomo" / f"{module_id}.list"
        path.write_text(text, encoding="utf-8")
        emitted.append({"path": str(path.relative_to(out)), "sha256": sha256(path), "module": module_id})

    if not emitted and not args.allow_empty:
        raise SystemExit("REFUSED: no canonical records satisfy the selected public release gate")

    public_manifest = {
        "schema_version": 1,
        "version": version,
        "channel": channel,
        "source": manifest["release"]["source_repository"],
        "artifacts": emitted,
        "skipped_non_publishable_modules": sorted(skipped),
        "assurance": "RC artifacts validate routing identification only; they do not guarantee account, authentication, fraud-control, or regional service eligibility.",
    }
    manifest_path = out / "manifest.json"
    manifest_path.write_text(json.dumps(public_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    sums = [f"{item['sha256']}  {item['path']}" for item in emitted]
    sums.append(f"{sha256(manifest_path)}  manifest.json")
    (out / "SHA256SUMS").write_text("\n".join(sums) + "\n", encoding="utf-8")
    print(f"STAGED {len(emitted)} {channel} artifact(s); skipped {len(skipped)} module(s)")
    return 0


if __name__ == "__main__": raise SystemExit(main())
