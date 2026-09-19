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
2. The v0.1 ABP normalizer accepts only plain domains and `||domain^` anchors; ABP anchors remain explicitly `SAFE_DEGRADE`.
3. Native hosts-file sources use a separate strict normalizer: null-route hostnames become exact canonical `domain` matchers with `EXACT` lowering and are never broadened to `domain_suffix`.
4. Exceptions, options, regex, wildcard and cosmetic syntax are not broadened into domain rejects.
5. Rejected source lines remain visible in an audit report.
6. Every accepted matcher keeps its source IDs, source-count, parser identity and semantic-lowering evidence.
7. Exact and hierarchical domain overlaps with existing non-Blocking canonical rules are withheld from the candidate set for review.
8. Explicit allowlist entries protect known-good domains from automatic Blocking candidacy; each allowlist record requires reason and evidence.
9. Candidate IDs are stable hashes of canonical matcher identity, so reviews cannot drift silently when source ordering changes.
10. A candidate becomes promotable only after a valid review record explicitly decides `block` and records service-overlap, root-domain and false-positive checks.
11. Missing, expired, duplicate, `allow`, or `hold` reviews never become promotable.
12. Candidate and review-gate outputs remain non-canonical; neither script edits `rules/blocking/blocking.yaml`.
13. Source registry inclusion does not grant redistribution permission.

## Next gates

Before any real upstream data becomes a canonical Blocking rule, Hrules still requires license/reuse review, source-specific URL/revision pinning, representative runtime validation, and an explicit promotion step from reviewed candidates into canonical records. The current pipeline intentionally stops before automatic promotion.


## Native exact-host source track

The first native-source track intentionally starts with host-file data whose semantics can be represented without broadening:

- `StevenBlack/hosts:data/StevenBlack/hosts` — Steven Black's own ad-hoc list, not the mixed-license aggregate product.
- `AdAway/adaway.github.io:hosts.txt` — the AdAway default hosts blocklist.

A hosts record such as `0.0.0.0 ads.example.com` identifies that hostname only. Hrules therefore lowers it to `domain: ads.example.com` with `EXACT` semantics. It does **not** infer that every subdomain of `ads.example.com` should also be rejected.

Both sources remain behind `redistribution_review: required`. License metadata in the registry records upstream terms, but Hrules will not publish derived data until attribution/reuse obligations are implemented and reviewed.
