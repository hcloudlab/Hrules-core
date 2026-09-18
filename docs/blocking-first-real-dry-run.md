# First real Blocking upstream dry run

Date: 2026-09-18 UTC

This record captures the first real-upstream execution of the Hrules Blocking ingestion pipeline. It is evidence only; no candidate in this run was promoted into `rules/blocking/blocking.yaml`.

## Inputs

- `easylist_china`: `easylist/easylistchina`, `master/easylistchina.txt`
- `adrules_adblock_list`: `Cats-Team/AdRules`, `main/dns.txt`

Both artifacts passed the snapshot anomaly guard before normalization.

## Observed snapshot

| Source | Bytes | Meaningful upstream entries | Strictly accepted | Rejected as unsupported | Reject ratio |
| --- | ---: | ---: | ---: | ---: | ---: |
| EasyList China | 546,055 | 18,000 | 5,621 | 12,379 | 68.77% |
| AdRules DNS | 4,761,835 | 199,747 | 199,309 | 438 | 0.22% |

Snapshot SHA-256:

- EasyList China: `0c18438ee3d63ec1ce4c1f511f529094eb3c9e9b3f1ae97cc7eb598cf0d54efb`
- AdRules DNS: `f3bc3cd08cc4cac437adac1c753f2c611369cfc1961520cdb3a5fb4c8d742711`

## Pipeline result

- Review-only candidates: **197,413**
- Withheld for overlap with existing Hrules canonical service rules: **1,923**
- Protected by current explicit allowlist: **0**
- Unsupported/rejected source lines retained as evidence: **12,817**

## Interpretation

The high EasyList China rejection ratio is expected under the intentionally narrow v0.1 normalizer: most browser-oriented ABP syntax is not assumed to be safely equivalent to a proxy-level domain REJECT. This is not treated as lost data; rejected lines remain audit evidence for future source-specific parsers.

The AdRules DNS artifact is much closer to the domain-level semantics Hrules can represent, so the strict parser accepts nearly all of it. That does **not** mean those domains are safe to publish automatically. The 197k candidate volume makes per-domain manual review impractical and demonstrates the need for a classification/risk sampling stage before canonical promotion.

The 1,923 overlaps are deliberately withheld. They are not automatically classified as upstream false positives: some are parent/child relationships caused by Hrules' conservative service-overlap policy and require analysis before any blocking decision.

## Decision

No real candidate is promoted by this dry run.

Before the first canonical Blocking batch, add:

1. source/category classification so a DNS aggregation list is not assumed to mean only `advertising`;
2. risk-based sampling and root-domain concentration analysis;
3. explicit licensing/reuse decision for each publishable source or derived artifact;
4. representative runtime false-positive validation;
5. bounded batch promotion rather than bulk promotion of the full candidate set.
