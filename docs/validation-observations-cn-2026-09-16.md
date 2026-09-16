# CN routing gap observations — 2026-09-16

These observations are discovery evidence from a live Clash Verge / Mihomo session using a real Jiuyun subscription. They are intentionally kept outside the canonical rule schema because observation alone does not authorize assignment to CN Direct.

## Confirmed matcher behavior

- `api.smoot.apple.cn` matched `DOMAIN-SUFFIX,cn` and routed `DIRECT`.
- This proves the `.cn` bootstrap matcher works, but not that it covers mainland traffic comprehensively.

## ByteDance / Douyin gap

Observed traffic that fell through `MATCH` to the default proxy included:

- `live.douyin.com`
- `douyinpic.com`
- `zjcdn.com`
- `bytegecko.com`
- `byteeffects.com`
- `huoshanstatic.com`
- `bytetcc.com`

Interpretation: a `.cn`-only baseline is insufficient for mainland services. These domains are candidate discovery evidence only; shared CDN or platform domains must not be assigned to CN Direct without source/provenance review and conflict analysis.

## CMB gap

Observed `lf12-32-gateway.paas.cmbchina.com` falling through `MATCH` to the default proxy.

Interpretation: discovery evidence only. Banking/service ownership and dependency classification require separate validation before canonical inclusion.

## Design consequence

Broad CN coverage should be supplied through an approved upstream adapter plus Hrules normalization, conflict checks and routing tests, rather than by manually adding domains observed in one session.
