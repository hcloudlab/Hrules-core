# Hrules Canonical Rule Schema v0.1

Status: design baseline

## Purpose

The canonical rule model is the source-of-truth representation inside Hrules Core. Client formats such as Mihomo, Shadowrocket, and sing-box are generated from this model. Client syntax is an output concern and must not leak into canonical rule data unless a capability constraint must be recorded explicitly.

The schema separates four questions that are often mixed together in public proxy configurations:

1. What traffic is this?
2. Why do we believe it belongs to this service/module?
3. What policy class should consume it?
4. How confidently has HCloudLab validated it?

A canonical record MUST NOT directly encode a concrete proxy node, subscription node name, or client-specific proxy-group syntax.

## Design rules

- One fact should have one canonical owner.
- Identification data and routing policy are separate.
- Upstream provenance is mandatory for imported/derived facts.
- HCloudLab-observed facts must record evidence and validation state.
- Shared third-party infrastructure is not claimed by a service merely because it appeared in one session capture.
- Broad keyword matching is treated as higher-risk than exact/domain-suffix ownership.
- Financial/account-sensitive modules require stricter validation than ordinary media/information modules.
- Generators may lower canonical rules into different client syntaxes, but may not silently broaden their semantic scope.

## Repository layout

```text
rules/
  services/
    ai/
      claude.yaml
      openai.yaml
      gemini.yaml
    crypto/
      binance.yaml
      coinbase.yaml
      kraken.yaml
      okx.yaml
      bybit.yaml
    banking/
      chase.yaml
      bank-of-america.yaml
      wells-fargo.yaml
      citi.yaml
      capital-one.yaml
      american-express.yaml
    stocks/
      brokerage/
        interactive-brokers.yaml
        schwab.yaml
        fidelity.yaml
        robinhood.yaml
        webull.yaml
      market-data/
        tradingview.yaml
        yahoo-finance.yaml
  baseline/
    private.yaml
    cn.yaml
    reject.yaml
```

This layout is logical, not a commitment that every listed module is ready for release.

## Module document

Each service file contains module metadata and canonical rule records.

```yaml
schema_version: 1
module:
  id: claude
  name: Claude
  category: ai
  policy_class: sensitive_account
  status: validating
  owners:
    - HCloudLab
  description: Traffic required for Claude web/app usage.

rules:
  - id: claude.domain.example
    match:
      type: domain_suffix
      value: example.com
    ownership: first_party
    purpose: service_core
    provenance:
      kind: first_party
      source: official_service
      reference: null
      observed_at: null
    evidence:
      level: verified
      methods:
        - official_domain
        - session_observation
    validation:
      state: passed
      tests:
        - web_access
        - auth_flow
    conflicts: []
    notes: null
```

## Required module fields

### `schema_version`

Integer schema version. Generators must reject unsupported future versions rather than guessing.

### `module.id`

Stable machine identifier. Lowercase kebab-case is preferred. This ID must remain stable even if the UI display name changes.

### `module.name`

Human-readable service/institution name.

### `module.category`

Initial controlled vocabulary:

- `ai`
- `crypto`
- `banking`
- `brokerage`
- `market_data`
- `media`
- `communication`
- `platform`
- `baseline`
- `blocking`

New categories require a schema/design review rather than ad-hoc spelling.

### `module.policy_class`

Describes routing requirements, not the final proxy group name.

Initial vocabulary:

- `ordinary_proxy`: ordinary proxied traffic; latency/availability may dominate.
- `region_preferred`: a region is preferred but cross-region fallback can be acceptable.
- `sensitive_account`: account/session traffic where egress consistency should be prioritized over global lowest latency.
- `direct_preferred`: traffic normally intended for direct routing.
- `reject`: blocking policy.
- `informational`: information/market-data traffic that must not automatically inherit account-sensitive routing merely because it belongs to the same business vertical.

Policy classes are inputs to client templates. They do not themselves select a country or node.

### `module.status`

- `research`
- `validating`
- `release_candidate`
- `published`
- `deprecated`

## Canonical rule record

### `id`

Stable unique rule ID. Recommended pattern:

`<module>.<match-type>.<normalized-value-or-short-id>`

IDs are for audit history and tests; generators must not depend on array order.

### `match.type`

Canonical match vocabulary v0.1:

- `domain`
- `domain_suffix`
- `domain_keyword`
- `ip_cidr`
- `ip_cidr6`
- `process_name`
- `process_path`

Client-specific constructs such as Mihomo `GEOSITE` or `RULE-SET` are not canonical atomic match types. They belong to source adapters or generated outputs unless Hrules explicitly models a referenced dataset as a separate canonical source object.

### `match.value`

Normalized match value. Domain names must be lowercase and must not contain URL schemes or paths. CIDRs must be canonical network notation.

### `ownership`

This field prevents a major class of over-routing errors.

- `first_party`: owned/controlled by the target service or institution.
- `dedicated_third_party`: third-party infrastructure demonstrably dedicated to the service/module.
- `shared_third_party`: shared identity/CDN/analytics/cloud infrastructure.
- `unknown`: ownership not yet established.

`shared_third_party` and `unknown` records are not publishable into a sensitive service module by default.

### `purpose`

Initial vocabulary:

- `service_core`
- `authentication`
- `api`
- `static_asset`
- `download`
- `realtime`
- `payment`
- `market_data`
- `telemetry`
- `analytics`
- `advertising`
- `unknown`

Purpose is descriptive. It does not independently decide routing.

## Provenance

Every record requires provenance.

```yaml
provenance:
  kind: upstream
  source: metacubex_meta_rules_dat
  reference: geosite/openai
  observed_at: 2026-09-17
```

Allowed `kind` values:

- `first_party`: verified from an official service-controlled source.
- `upstream`: imported or derived from a registered upstream rules project.
- `hcloudlab_observation`: observed in HCloudLab DNS/connection/session testing.
- `community_report`: reported externally but not independently validated.
- `manual_research`: manually researched evidence that does not fit the above categories.

`source` must resolve either to `sources/registry.yaml` or to an Hrules-controlled evidence identifier.

A URL alone is not proof of ownership. `reference` is an audit pointer, not an evidence score.

## Evidence levels

```yaml
evidence:
  level: verified
  methods:
    - official_domain
    - session_observation
```

Levels:

- `candidate`: discovered but not trusted for release.
- `corroborated`: supported by more than one meaningful source/method but not yet fully validated in HCloudLab routing tests.
- `verified`: evidence and required validation satisfy the module's release policy.

Suggested methods:

- `official_domain`
- `official_documentation`
- `upstream_ruleset`
- `dns_observation`
- `connection_log`
- `session_observation`
- `app_observation`
- `manual_review`

Evidence level must be computed/approved by validation policy; generators must not infer `verified` merely from the number of methods.

## Validation state

```yaml
validation:
  state: passed
  last_tested: 2026-09-17
  tests:
    - web_access
    - auth_flow
    - api_flow
```

States:

- `untested`
- `partial`
- `passed`
- `failed`
- `stale`

A record may have strong provenance but still be `untested`. Provenance and runtime validation are intentionally separate axes.

Sensitive modules should require more than root-domain reachability. Their module-level release gate should exercise the relevant session flow.

## Conflicts

```yaml
conflicts:
  - module: google
    relation: overlap
    resolution: claude_precedence
```

Conflict relations:

- `duplicate`: semantically identical canonical ownership.
- `overlap`: one matcher can catch traffic also claimed elsewhere.
- `dependency`: module relies on traffic primarily owned by another module.
- `policy_conflict`: the same matcher would receive incompatible routing policies.

Every unresolved `policy_conflict` blocks publication.

## Exclusions

Modules may explicitly record exclusions when broad upstream sources contain traffic Hrules does not want to inherit.

```yaml
exclusions:
  - match:
      type: domain_suffix
      value: example-market-data.com
    reason: market_data_must_not_inherit_exchange_account_policy
```

Exclusions are especially important when adapting broad Crypto, AI, or platform datasets.

## Module-level validation policy

A module may define stricter release requirements:

```yaml
release_policy:
  minimum_evidence: verified
  allowed_ownership:
    - first_party
    - dedicated_third_party
  required_tests:
    - web_access
    - auth_flow
  forbid_unresolved_policy_conflicts: true
```

For `sensitive_account`, the default release policy should forbid `shared_third_party` and `unknown` unless an explicit reviewed exception exists.

## Example: brokerage versus market data

Hrules must not model an entire business vertical as one routing fact.

```text
Interactive Brokers login/API -> brokerage -> sensitive_account
TradingView market data       -> market_data -> informational
```

Both may be described by users as “美股”, but they have different routing requirements. The public UI may aggregate choices where useful; the canonical layer must preserve the distinction.

## Example: Crypto

The canonical layer should preserve exchange identity:

```text
binance/*  -> crypto/binance
coinbase/* -> crypto/coinbase
kraken/*   -> crypto/kraken
```

The Mihomo v0.1 template may route these modules into one visible `💰 虚拟货币 [自选]` policy group. That aggregation happens in the template/policy layer, not by destroying service identity in canonical data.

## Example: AI

```text
claude/* -> ai/claude  -> sensitive_account policy class
openai/* -> ai/openai  -> sensitive_account policy class
gemini/* -> ai/gemini  -> region_preferred or template-defined AI policy
```

The exact user-facing proxy groups remain a template decision.

## Generation contract

Canonical input:

```text
service identity + atomic match + ownership + purpose + provenance + evidence + validation + conflicts
```

Policy/template input:

```text
module -> policy class -> user-facing strategy group -> region/system groups
```

Generated output:

```text
Mihomo RULE-SET / GEOSITE / DOMAIN-SUFFIX ...
Shadowrocket RULE-SET / DOMAIN-SUFFIX ...
sing-box rule_set / domain_suffix ...
```

Generators MUST:

1. validate schema before generation;
2. exclude non-publishable records;
3. apply explicit exclusions;
4. detect duplicates and policy conflicts;
5. preserve deterministic ordering;
6. emit provenance/version manifests;
7. fail closed when a canonical matcher cannot be represented safely in the target client.

Generators MUST NOT silently convert an unsupported precise matcher into a broader matcher.

## Publication gate v0.1

A canonical module is eligible for generated public artifacts only when:

- schema validation passes;
- all emitted records have provenance;
- license/reuse policy is cleared for upstream-derived records;
- no unresolved policy conflicts remain;
- module release-policy requirements pass;
- representative routing tests pass;
- generated client syntax validates;
- output manifest and SHA256 are produced.

## What is intentionally not in the canonical schema

The following belong elsewhere:

- concrete proxy node names;
- airport/subscription provider names;
- `url-test` intervals and tolerance;
- region regexes;
- Mihomo proxy-group topology;
- DNS/fake-ip configuration;
- TUN configuration;
- UI emojis/display order;
- final `MATCH` behavior.

Those are client-template and routing-policy concerns. Keeping them out of canonical rules is what allows one Hrules knowledge base to generate multiple clients without duplicating service facts.

## Next implementation step

Create a machine-validated schema (`schemas/canonical-rule.schema.json`) matching this design, then create a small fixture set rather than bulk-importing rules:

- Claude
- OpenAI
- Gemini
- one crypto exchange
- one brokerage
- one market-data service
- CN/private baseline

Use those fixtures to prove validation, conflict detection, and Mihomo/Shadowrocket/sing-box generation before expanding coverage.
