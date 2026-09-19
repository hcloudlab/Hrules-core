# Blocking ingestion pipeline

Blocking data is not copied from an upstream list into a public Hrules artifact.

The current pipeline is deliberately review-only:

```text
upstream
  -> upstream_guard.py
  -> immutable snapshot + checksum metadata
  -> strict source normalizer
  -> rejected-syntax evidence
  -> cross-source deduplication/corroboration
  -> hierarchical collision check against existing canonical service rules
  -> explicit protected-domain allowlist
  -> review-only candidate JSON with stable candidate IDs
  -> false-positive review record
  -> review gate
  -> canonical Blocking module
  -> client lowering + tests
  -> release gate
```

## Safety properties

1. A source snapshot that is unexpectedly tiny or collapses relative to the previous snapshot is refused.
2. The v0.1 ABP normalizer accepts only plain domains and exact `||domain^` anchors.
3. Exceptions, options, regex, wildcard and cosmetic syntax are not broadened into domain rejects.
4. Rejected source lines remain visible in an audit report.
5. Every accepted matcher keeps its source IDs and source-count.
6. Exact and hierarchical domain overlaps with existing non-Blocking canonical rules are withheld from the candidate set for review.
7. Explicit allowlist entries protect known-good domains from automatic Blocking candidacy; each allowlist record requires reason and evidence.
8. Candidate IDs are stable hashes of canonical matcher identity, so reviews cannot drift silently when source ordering changes.
9. A candidate becomes promotable only after a valid review record explicitly decides `block` and records service-overlap, root-domain and false-positive checks.
10. Missing, expired, duplicate, `allow`, or `hold` reviews never become promotable.
11. Candidate and review-gate outputs remain non-canonical; neither script edits `rules/blocking/blocking.yaml`.
12. Source registry inclusion does not grant redistribution permission.

## Next gates

Before any real upstream data becomes a canonical Blocking rule, Hrules still requires license/reuse review, source-specific URL/revision pinning, representative runtime validation, and an explicit promotion step from reviewed candidates into canonical records. The current pipeline intentionally stops before automatic promotion.
