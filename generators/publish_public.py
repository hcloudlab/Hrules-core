#!/usr/bin/env python3
"""Build the public Hrules release tree from canonical records.

The release manifest determines the channel. RC publication proves routing
identification only; stable publication requires each module's complete declared
validation set. Public Mihomo rule-provider payloads are intentionally policy-free:
service identity is emitted separately from user-facing routing groups.
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
PROFILE_VALIDATOR_PATH = ROOT / "scripts" / "validate_profiles.py"

spec = importlib.util.spec_from_file_location("compile_rules", COMPILER_PATH)
compiler = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(compiler)

profile_spec = importlib.util.spec_from_file_location("validate_profiles", PROFILE_VALIDATOR_PATH)
profile_model = importlib.util.module_from_spec(profile_spec)
assert profile_spec and profile_spec.loader
profile_spec.loader.exec_module(profile_model)


def load_yaml(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def write_mihomo_provider(path: Path, matchers: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = yaml.safe_dump({"payload": matchers}, allow_unicode=True, sort_keys=False)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--rules", default="rules")
    p.add_argument("--policy", default="policies/v0.1.yaml")
    p.add_argument("--profiles", default="profiles/v0.1.yaml")
    p.add_argument("--release-manifest", default="manifests/v0.1-release-candidate.yaml")
    p.add_argument("--out", default="build/public-release")
    p.add_argument("--allow-empty", action="store_true", help="CI/testing only")
    args = p.parse_args()

    manifest = load_yaml(Path(args.release_manifest))
    version = manifest["release"]["version"]
    channel = "rc" if "-rc" in version else "stable"
    policy = load_yaml(Path(args.policy))
    profile_doc = load_yaml(Path(args.profiles))
    modules = compiler.load_modules(Path(args.rules))
    modules_by_id = {module["module"]["id"]: module for module in modules}

    out = Path(args.out)
    if out.exists():
        shutil.rmtree(out)
    (out / "mihomo" / "rules").mkdir(parents=True, exist_ok=True)

    emitted, skipped = [], []
    emitted_modules: set[str] = set()

    for module_id, module in sorted(modules_by_id.items()):
        selected = [rule for rule in module["rules"] if compiler.publishable(module, rule, channel)]
        selected = [rule for rule in selected if compiler.exclusion_action(rule, module.get("exclusions", [])) == "keep"]
        if not selected:
            skipped.append(module_id)
            continue

        # Force an explicit policy binding even though provider payloads themselves
        # do not contain the destination group.
        compiler.target_name(module_id, policy)
        matchers = [compiler.mihomo_matcher(rule) for rule in selected]
        path = out / "mihomo" / "rules" / f"{module_id}.yaml"
        write_mihomo_provider(path, matchers)
        emitted_modules.add(module_id)
        emitted.append({
            "path": str(path.relative_to(out)),
            "sha256": sha256(path),
            "module": module_id,
            "client": "mihomo",
            "format": "rule-provider/classical",
            "entries": len(matchers),
        })

    if not emitted and not args.allow_empty:
        raise SystemExit("REFUSED: no canonical records satisfy the selected public release gate")

    canonical_ids = set(modules_by_id)
    profile_state = []
    for profile_id, item in profile_doc["profiles"].items():
        resolved = profile_model.resolve_profile(profile_id, profile_doc["profiles"], canonical_ids)
        missing = sorted(set(resolved) - emitted_modules)
        available = [module_id for module_id in resolved if module_id in emitted_modules]
        profile_state.append({
            "id": profile_id,
            "title": item["title"],
            "complete": not missing,
            "modules": resolved,
            "available_modules": available,
            "withheld_modules": missing,
        })

    public_manifest = {
        "schema_version": 2,
        "version": version,
        "channel": channel,
        "source": manifest["release"]["source_repository"],
        "artifacts": emitted,
        "skipped_non_publishable_modules": sorted(skipped),
        "profiles": profile_state,
        "clients": profile_doc.get("clients", {}),
        "assurance": "RC artifacts validate routing identification only; they do not guarantee account, authentication, fraud-control, or regional service eligibility.",
    }
    manifest_path = out / "manifest.json"
    manifest_path.write_text(json.dumps(public_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    sums = [f"{item['sha256']}  {item['path']}" for item in emitted]
    sums.append(f"{sha256(manifest_path)}  manifest.json")
    (out / "SHA256SUMS").write_text("\n".join(sums) + "\n", encoding="utf-8")

    complete_profiles = [p["id"] for p in profile_state if p["complete"]]
    incomplete_profiles = [p["id"] for p in profile_state if not p["complete"]]
    print(f"STAGED {len(emitted)} {channel} provider artifact(s); skipped {len(skipped)} module(s)")
    print(f"COMPLETE PROFILES: {', '.join(complete_profiles) if complete_profiles else '(none)'}")
    print(f"WITHHELD/INCOMPLETE PROFILES: {', '.join(incomplete_profiles) if incomplete_profiles else '(none)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
