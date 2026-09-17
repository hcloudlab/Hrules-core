# US Banking Validation Baseline — 2026-09-16

## Scope

This record captures HCloudLab observations from real Clash Verge / Mihomo sessions using a Jiuyun subscription. It is evidence for rule development, not a claim that all listed banks are release-ready.

## Bank of America

Observed first-party namespace: `bankofamerica.com`.

Representative observed hosts included:
- `www.bankofamerica.com`
- `secure.bankofamerica.com`
- `tilt.bankofamerica.com`
- `chat.bankofamerica.com`
- `chatevents.bankofamerica.com`
- `glassbox-hlx-igw.bankofamerica.com`
- `rail.bankofamerica.com`
- `boss.bankofamerica.com`
- `aero.bankofamerica.com`
- `dull.bankofamerica.com`

Dedicated Test 5 routing succeeded:

`bankofamerica.com -> 🏦 美国银行 [自选] -> 🇺🇸 美国 [系统] -> Jiuyun US node`

Shared third-party traffic such as CookieLaw, OneTrust, Google/Google Tag Manager/Google Ads and STUN/CDN traffic remained on default routing. This separation is intentional.

Status: web routing validated; authentication flow not yet validated.

## Chase

Observed under the first-party `chase.com` namespace:
- `measure.chase.com`
- `analytics.chase.com`
- `chase-ipma-lucy.chase.com`
- `static.chase.com`
- `securej.chase.com`

Current evidence is session observation only. Final Hrules routing is pending the single consolidated acceptance test.

## Wells Fargo

Observed first-party namespace:
- `wellsfargo.com`

Representative hosts:
- `www.wellsfargo.com`
- `static.wellsfargo.com`
- `connect.secure.wellsfargo.com`
- `oam.wellsfargo.com`

Additional observed candidates:
- `www10.wellsfargomedia.com`
- `www17.wellsfargomedia.com`
- exact host `connect.secure.wf.com`

The broad `wf.com` namespace is deliberately not claimed. The exact observed `connect.secure.wf.com` host is retained as a research candidate until ownership/necessity is confirmed.

## Citi

An access attempt to `www.citi.com` reached a permission-denied page referencing `errors.edgesuite.net`.

This does not establish the cause. Hrules does not infer that the denial was caused by the selected exit IP, geography, IP reputation, CDN policy, or Hrules itself without a controlled comparison.

`errors.edgesuite.net` is not assigned to Citi.

## Capital One

Official Capital One banking/account pages confirm `capitalone.com` as the first-party namespace. Runtime Hrules validation is pending.

## American Express

Official American Express login/account pages confirm `americanexpress.com` as the first-party namespace. Runtime Hrules validation is pending.

## Consolidated final test

To minimize account-risk noise and avoid repeated exit changes, no more intermediate real-account testing should be performed. The next real test should be a single consolidated acceptance pass after CI is green.

Acceptance targets:
1. Claude/OpenAI stays on the selected stable sensitive-AI exit.
2. YouTube main and playback traffic uses `hrules-youtube`.
3. Mainland CN traffic uses `hrules-cn -> DIRECT` where covered.
4. Bank of America, Chase, Wells Fargo, Citi, Capital One and American Express first-party rules map to `🏦 美国银行 [自选]`.
5. Wells Fargo candidate dependencies are checked without broadening `wf.com` prematurely.
6. Shared third-party traffic is not silently absorbed into sensitive banking policy.
7. Final `MATCH` remains the fallback for uncategorized traffic.
