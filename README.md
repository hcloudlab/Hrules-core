# Hrules Core

Private build and validation repository for HCloudLab Rules.

## Purpose

Hrules Core maintains rule-source metadata, normalization logic, client templates, validation tests, and release manifests. Public artifacts are published separately to `hcloudlab/Hrules` only after validation.

## Current status

The Mihomo / Clash Verge v0.1 architecture and validation baseline is now a **release candidate**. The consolidated runtime acceptance record is `docs/validation/final-acceptance-2026-09-16.md`, and the release-candidate manifest is `manifests/v0.1-release-candidate.yaml`.

The public `hcloudlab/Hrules` repository remains the publication boundary: private/core research state must not be exposed directly. Only validated artifacts, public documentation, provenance/attribution metadata, version information and hashes should cross that boundary.

## Initial client targets

1. Mihomo / Clash Verge — v0.1 release candidate
2. Shadowrocket — next client output target
3. sing-box / SFM — next client output target

## Design principles

- One normalized rule model, multiple client outputs.
- Upstream updates never publish directly to users.
- Separate rule data from routing policy and proxy-group design.
- Prefer mature upstream rule projects over maintaining large domain lists manually.
- Preserve source attribution and license metadata for every imported or derived ruleset.
- Every release must pass syntax, conflict, and representative routing tests.
- Public download URLs should remain stable while versioned artifacts and hashes remain auditable.
- Sensitive-service routing means controlled/predictable egress; it does not claim to prevent account risk, fraud controls, bans, or service-side decisions.
- Shared third-party/CDN/analytics domains are not classified into sensitive modules solely because they appear during a service session.

## Release pipeline

Upstream sources -> fetch -> normalize -> deduplicate -> conflict checks -> generate client outputs -> syntax validation -> routing tests -> manifest/SHA256 -> publish to Hrules.

A release candidate may advance to the public repository only when the applicable CI gates are green and the release manifest identifies the validated scope. Research-only modules or evidence must not be presented publicly as fully validated behavior.

## Repository areas

- `sources/`: upstream source registry and licensing metadata
- `rules/`: normalized Hrules rule definitions and HCloudLab overrides
- `templates/`: client-specific configuration templates
- `generators/`: generation/conversion code
- `tests/`: syntax, conflict, and routing validation
- `manifests/`: version, release scope and provenance manifests
- `docs/`: architecture decisions, research notes and runtime validation records
- `.github/workflows/`: CI and release automation
