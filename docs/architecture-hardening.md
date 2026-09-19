# Architecture hardening: routing precedence and client lowering

This document records invariants introduced after the v0.1 cross-review.

## 1. Routing precedence is semantic

Filesystem paths and filenames MUST NOT determine routing precedence.

Logical policies declare a `routing_stage`; `policies/v0.1.yaml` maps stages to numeric order. Compilers sort canonical modules by that semantic stage before emitting first-match rule lists.

Current stage model:

```text
private
  ↓
blocking
  ↓
sensitive_service
  ↓
ordinary_service
  ↓
cn_domain
  ↓
cn_ip
  ↓
fallback
```

A new policy without a valid routing stage is a validation failure.

## 2. Exclusions are executable constraints

`exclusions` are not documentation-only metadata.

- If an exclusion exactly matches, or safely contains, a canonical rule, that rule is suppressed.
- If an exclusion is narrower than a broader canonical matcher, compilation fails closed because subtractive semantics cannot be represented by simply emitting the broad rule.

Example: a `domain_suffix: example.com` rule with an exclusion for `login.example.com` cannot be lowered safely as one ordinary suffix rule. The compiler must stop rather than overmatch.

## 3. Client lowering contract

Every canonical matcher/client pair has one of three semantic states:

- `EXACT` — the target can express the canonical matcher with the intended semantics.
- `SAFE_DEGRADE` — a known, documented semantic difference is accepted for that target.
- `UNSUPPORTED` — safe lowering is unavailable; compilation fails closed.

No adapter may silently turn `UNSUPPORTED` into a broader matcher.

Current Shadowrocket and sing-box compilers remain experimental until real-client acceptance is recorded. CLI generation for experimental targets requires an explicit `--allow-experimental` flag.

## 4. Conflict detection

Cross-module conflict checks cover:

- exact matcher duplicates,
- domain/domain-suffix containment,
- IPv4 CIDR overlap,
- IPv6 CIDR overlap.

Overlaps across different policy classes block validation.

## 5. Release invariant

A generated file is not considered supported merely because serialization succeeded. Public client support requires syntax validation where available and real-client acceptance for the advertised client/version.
