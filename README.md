# Hrules Core

Private build and validation repository for HCloudLab Rules.

## Purpose

Hrules Core maintains rule-source metadata, normalization logic, client templates, validation tests, and release manifests. Public artifacts are published separately to `hcloudlab/Hrules` only after validation.

## Initial client targets

1. Mihomo / Clash Verge
2. Shadowrocket
3. sing-box / SFM

## Design principles

- One normalized rule model, multiple client outputs.
- Upstream updates never publish directly to users.
- Separate rule data from routing policy and proxy-group design.
- Prefer mature upstream rule projects over maintaining large domain lists manually.
- Preserve source attribution and license metadata for every imported or derived ruleset.
- Every release must pass syntax, conflict, and representative routing tests.
- Public download URLs should remain stable while versioned artifacts and hashes remain auditable.

## Planned pipeline

Upstream sources -> fetch -> normalize -> deduplicate -> conflict checks -> generate client outputs -> syntax validation -> routing tests -> manifest/SHA256 -> publish to Hrules.

## Repository areas

- `sources/`: upstream source registry and licensing metadata
- `rules/`: normalized Hrules rule definitions and HCloudLab overrides
- `templates/`: client-specific configuration templates
- `generators/`: generation/conversion code
- `tests/`: syntax, conflict, and routing validation
- `manifests/`: version and provenance manifests
- `docs/`: architecture decisions and research notes
- `.github/workflows/`: CI and release automation

No public release is produced from this repository until the first architecture and validation baseline is complete.
