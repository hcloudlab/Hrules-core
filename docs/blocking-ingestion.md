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
  -> collision check against existing canonical service rules
  -> review-only candidate JSON
  -> human/evidence review
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
6. Exact collisions with existing non-Blocking canonical rules are withheld from the candidate set for review.
7. Candidate output is explicitly `review_only`; the ingestion script never edits `rules/blocking/blocking.yaml`.
8. Source registry inclusion does not grant redistribution permission.

## Next gates

Before any real upstream data becomes a canonical Blocking rule, Hrules still requires license/reuse review, source-specific URL/revision pinning, broader overlap/allowlist analysis, false-positive review and representative runtime validation.
