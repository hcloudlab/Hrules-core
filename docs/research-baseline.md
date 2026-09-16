# Hrules Research Baseline

Status: initial architecture research, 2026-09-16.

## Projects examined

### MetaCubeX/meta-rules-dat

Role: Mihomo-oriented GeoIP/GeoSite/rule-set data distribution, with a separate sing-box rule-set branch.

Observed design lessons:
- Publishes multiple data formats rather than coupling rules to one GUI client.
- Provides Mihomo rule-set output and sing-box output separately.
- Aggregates data from several upstream projects.
- Uses specialized categories such as CN, YouTube, Google, OpenAI, Telegram, Netflix, etc.
- Suitable as an important upstream candidate, especially for Mihomo/sing-box, but its GPL-3.0 licensing must be handled explicitly before redistribution/derivation.

### Loyalsoldier/clash-rules

Role: generated Clash RULE-SET distribution.

Observed design lessons:
- Automated daily builds.
- Clearly separates domain, IP-CIDR, private, reject, direct and application categories.
- Documents upstream provenance.
- Demonstrates the mature pattern: source data -> automated build -> release branch -> stable raw/CDN URLs.
- Its example white-list routing model ends unmatched traffic at proxy, while explicit direct/private/CN rules precede fallback.
- GPL-3.0 licensing must be handled explicitly before redistribution/derivation.

### ACL4SSR/ACL4SSR

Role: long-running Clash/ACL rule collection with many service-specific fragments and complete configuration examples.

Observed design lessons:
- Useful for studying rule granularity and historical proxy-policy grouping patterns.
- Contains separate fragments for Apple, China domains/IPs, downloads, advertising and many service categories.
- Large monolithic/legacy configuration examples should not be copied as Hrules defaults; Hrules should target current Mihomo semantics and keep user-facing policy simpler.
- Repository metadata reports CC-BY-SA-4.0; attribution/share-alike implications must be reviewed before deriving public artifacts.

### blackmatrix7/ios_rule_script

Role: large cross-client rule aggregation project.

Observed design lessons:
- Strong evidence that one logical rule catalog can be emitted for multiple clients.
- Explicit client directories include Clash, Loon, Quantumult X, Shadowrocket and Surge.
- This supports Hrules' core architectural decision: normalized source concepts should be independent from client output format.
- Repository is GPL-2.0 and README also contains additional usage statements; do not copy/repackage its rule files into Hrules until licensing/usage implications are reviewed.

### n0de-sudo/Perfect-Rules

Role: user-oriented Mihomo/Clash configuration with simple self-select service groups and automatic regional groups.

Observed design lessons:
- Good UX pattern: user-facing service groups vs system-managed regional/automatic groups.
- Remote rule providers keep the main configuration understandable.
- Representative ordering: process/software -> private -> ads -> service-specific rules -> CN direct -> final default proxy.
- Hrules should learn from the UX architecture but independently design and validate its rule sources, groups and ordering.

## Initial Hrules decisions

1. Hrules Core is the source of truth; public Hrules is a release surface.
2. Rule data, routing policy, and proxy-group topology are three separate layers.
3. Initial outputs: Mihomo/Clash Verge, Shadowrocket, sing-box/SFM.
4. Do not manually curate thousands of common domains when mature upstream data exists.
5. Do not blindly aggregate upstream files. Every upstream source must have provenance, license, expected format, update policy and validation status recorded.
6. Upstream changes enter a staging build first. Public release requires validation.
7. Hrules-specific overrides should be small, documented and backed by reproducible observations/tests.
8. User-facing templates should prioritize: import works first; common routing works by default; users only choose policies where a choice is genuinely useful.

## Candidate logical policy layers

This is a research hypothesis, not yet a released configuration:

1. Explicit Hrules overrides / high-priority exceptions
2. Private/LAN direct
3. Blocking policy where enabled
4. AI services
5. Streaming/media services
6. Communication services
7. Platform/ecosystem services where separate policy is useful
8. Mainland-China direct domain rules
9. Mainland-China direct IP rules
10. Final default policy

Exact service categories and ordering must be validated before v0.1.

## Next research tasks

- Compare current Mihomo-native proxy-group patterns (`select`, `url-test`, fallback/load-balance where relevant) across maintained configurations.
- Determine whether AI should be one group with optional Claude/OpenAI overrides or separate default groups.
- Define regional node classification regexes and failure behavior.
- Define a canonical normalized rule schema that can generate Mihomo, Shadowrocket and sing-box outputs without losing semantics.
- Build a source/license registry before importing any upstream rule data.
- Define representative routing tests (Claude/OpenAI/YouTube/Telegram/CN/private/unmatched) and negative/conflict tests.
