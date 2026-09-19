# Blocking source license review

This document records the evidence used by Hrules to classify source-license obligations. It is a project review record, not legal advice.

## StevenBlack first-party hosts

- Repository: `StevenBlack/hosts`
- Hrules artifact: `data/StevenBlack/hosts`
- Upstream metadata: `data/StevenBlack/update.json` identifies this source as `MIT`.
- The repository also exposes `license.txt` and package metadata identifying MIT.
- Hrules status: `redistribution_review: required`
- Hrules handling: attribution/license notice must be carried before any derived publication is cleared.
- Scope decision: Hrules uses Steven Black's own source file, not the generated aggregate hosts product, because the aggregate incorporates multiple upstream lists with separate licenses.

## AdAway default hosts

- Repository: `AdAway/adaway.github.io`
- Hrules artifact: `hosts.txt`
- The file header states `CC Attribution 3.0`.
- Hrules status: `redistribution_review: required`
- Hrules handling: attribution must be implemented before any derived publication is cleared.

## Release invariant

License identification is not equivalent to redistribution clearance.

A source may be:
1. registered for research,
2. fetched and normalized for review-only evidence,
3. used to build non-canonical review packets,

while still being forbidden from public Hrules output.

The source registry must remain fail-closed until attribution/reuse obligations are implemented and explicitly cleared.
