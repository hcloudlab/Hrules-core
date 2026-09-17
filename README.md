# Hrules Core

Private build and validation repository for HCloudLab Rules.

## Purpose

Hrules Core maintains the canonical service-identification rules, provenance, validation evidence, scenario profiles, client compilers, tests and release manifests used to build the public `hcloudlab/Hrules` repository.

The public repository is a **multi-client × multi-scenario** distribution layer. Canonical rule facts are maintained once in Core and are never duplicated manually per client or per scenario.

## Product model

Hrules is organized on two independent axes:

1. **Scenario profile** — what the user needs to access.
2. **Client / engine output** — how the same routing intent must be represented for that client.

Current scenario baseline:

- `basic` — ordinary browsing, YouTube and common overseas services.
- `ai` — Basic + Claude / ChatGPT / Gemini.
- `us-finance` — AI + U.S. banking / brokerage / market data.
- `crypto` — AI + major crypto exchanges.
- `finance-pro` — U.S. Finance + Crypto.
- `full` — all Hrules modules for advanced/custom use.

Current client roadmap:

- Mihomo family: Clash Verge, Clash Mi.
- Shadowrocket.
- sing-box family: SFM / sing-box.
- v2rayN.
- Karing.

A client becomes public only after its generated output passes real-client acceptance. A profile becomes public only when the modules required by that profile satisfy the release gate for the advertised channel.

## Core invariants

- One normalized rule model, multiple client outputs.
- Scenario profiles reference canonical module IDs; they never copy domain/IP facts.
- Client compilers translate canonical matchers and logical policies; they do not own service identity.
- Upstream changes never publish directly to users.
- Rule identification is separate from routing policy and proxy-group design.
- Sensitive-service routing means controlled/predictable egress; it does not claim to prevent account risk, fraud controls, bans, or service-side decisions.
- Shared third-party/CDN/analytics domains are not classified into sensitive modules solely because they appear during a service session.
- Unsupported matcher lowering fails closed.
- Research-only or incomplete modules must never be presented publicly as fully validated behavior.

## Current status

The Mihomo / Clash Verge v0.1 architecture and routing-validation baseline is a **release candidate**. The consolidated runtime acceptance record is `docs/validation/final-acceptance-2026-09-16.md`, and the release-candidate manifest is `manifests/v0.1-release-candidate.yaml`.

The initial RC artifact demonstrates validated routing-identification coverage only. Stable publication remains stricter and requires each module's declared validation requirements.

The public `hcloudlab/Hrules` repository remains the publication boundary. Private/core research state must not be exposed directly. Only validated client artifacts, user-facing profiles, public documentation, provenance/attribution metadata, version information and hashes may cross that boundary.

## Release pipeline

Upstream sources -> fetch -> normalize -> deduplicate -> conflict checks -> canonical validation -> profile validation -> client compilation -> syntax validation -> representative routing tests -> real-client acceptance -> manifest/SHA256 -> publish to Hrules.

## Repository areas

- `sources/`: upstream source registry and licensing metadata
- `rules/`: normalized canonical Hrules rule definitions and HCloudLab overrides
- `policies/`: canonical-module to logical-routing-policy mapping
- `profiles/`: user-facing scenario manifests and client support matrix
- `templates/`: client-specific configuration templates
- `generators/`: client compilers and publication generators
- `scripts/`: validators and release checks
- `tests/`: syntax, conflict, profile, compiler and routing validation
- `manifests/`: version, release scope and provenance manifests
- `docs/`: architecture decisions, research notes and runtime validation records
- `.github/workflows/`: CI and release automation
