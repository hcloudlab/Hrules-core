# Hrules v0.1 consolidated runtime acceptance — 2026-09-16

## Scope

This record consolidates the real Clash Verge / Mihomo observations captured during the v0.1 acceptance session. It is evidence of routing behavior observed in that session, not a claim that any routing policy prevents account checks, fraud controls, bans, or service-side risk decisions.

## Confirmed routing observations

### Sensitive AI

Observed `chatgpt.com` routed through `🔐 Claude / OpenAI [自选]` and the selected US regional path. Earlier acceptance observations also covered Claude/OpenAI first-party routing. No additional repeated account testing is required for this v0.1 acceptance cycle.

### YouTube

Observed YouTube traffic, including `youtube.com` family traffic, routed through the Hrules YouTube rule provider and `📺 YouTube [自选]`.

### CN direct

Observed multiple Chinese service domains, including iQIYI / WeChat / QQ-family traffic, routed through `hrules-cn` to `DIRECT`.

### US banking

Observed dedicated banking-policy routing for first-party/candidate domains including:

- Bank of America: `secure.bankofamerica.com`, `w3f6gq.bankofamerica.com`
- American Express: `americanexpress.com`
- Capital One: `capitalone.com`
- Wells Fargo candidate exact host: `connect.secure.wf.com`

Earlier validation in this cycle also established `bankofamerica.com` first-party suffix behavior and separated shared third-party traffic from the banking policy.

Shared third-party/CDN/analytics namespaces are not automatically classified as banking traffic merely because they appear during a banking session.

### Crypto exchanges

Observed:

- Coinbase: `login.coinbase.com` -> `💰 虚拟货币 [自选]`
- Bybit: `www.bybit.com`, `ws2.bybit.com` -> `💰 虚拟货币 [自选]`
- Kraken: `api.kraken.com`, `api.seg.kraken.com` -> `💰 虚拟货币 [自选]`

A real observation found `stream.binance.us:9443` falling through `MATCH`. The canonical Binance module was therefore extended with `DOMAIN-SUFFIX,binance.us` and a regression assertion was added. This correction is validated offline by CI; no additional sensitive-account login is required for this acceptance cycle.

### Brokerage / stocks

Observed `interactivebrokers.com` traffic routed through `📈 美股 [自选]`. A real observation found `t.ibkr.com:443` falling through `MATCH`; the Interactive Brokers module was extended with `DOMAIN-SUFFIX,ibkr.com` and a regression assertion was added. This correction is validated offline by CI.

### Default fallback

Unclassified ordinary traffic continued to reach final `MATCH -> 🚀 默认代理 [自选]`, demonstrating that the new sensitive-service modules did not convert unrelated traffic into banking/crypto/AI routes.

## Regression corrections produced by acceptance

1. Added `binance.us` to the Binance crypto module after observing `stream.binance.us:9443` miss the crypto policy.
2. Added `ibkr.com` to the Interactive Brokers brokerage module after observing `t.ibkr.com:443` miss the stocks policy.
3. Added generated-Mihomo regression assertions for both domains.
4. Kept `connect.secure.wf.com` exact rather than broadening to all of `wf.com` without sufficient ownership/necessity evidence.

## CI gate

After correcting canonical-schema vocabulary for the new observations, the full Hrules Core validation pipeline passed, including canonical validation, policy mapping, conflict detection, semantic/compiler tests, MetaCubeX adapter tests, provider-mode builds/transforms, Mihomo topology/routing assertions, and Mihomo syntax validation.

## Acceptance conclusion

The v0.1 architecture has real runtime evidence for the principal routing classes: sensitive AI, YouTube, CN direct, US banking, crypto, brokerage/stocks, and default fallback. The two misses discovered in the final session were converted into canonical rules plus regression tests and can be accepted through offline CI without repeatedly exercising sensitive user accounts.
