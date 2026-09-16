# Hrules Mihomo v0.1 Design

Status: architecture baseline

## 1. Goal

Hrules v0.1 should be usable immediately after import while keeping routing understandable and controllable for non-expert users.

The central model is:

> Service identification -> service policy -> egress policy -> actual proxy node

Rule data and routing policy are separate. A service can move to another policy group later without rebuilding its domain/IP ruleset.

## 2. Design principles

1. Rules decide **who the traffic is**; proxy groups decide **where it goes**.
2. Common services should work without users understanding thousands of rules.
3. User-facing groups expose meaningful choices; implementation groups stay system-managed where possible.
4. Sensitive services must not be forced to use static, residential, ISP, or US IPs.
5. A stable airport/subscription node is a valid egress when it meets the user's needs.
6. ISP/residential and dedicated/fixed nodes are optional egress choices, not prerequisites.
7. For egress-sensitive services, avoid unintentional cross-region or cross-node changes.
8. Automatic selection is preferably performed **inside an intentionally selected region**, rather than globally across regions.
9. Empty optional capabilities must not make an ordinary user's configuration fail to load.

## 3. User-facing service groups

Initial v0.1 groups:

- `🔐 Claude / OpenAI [自选]`
- `🤖 AI 服务 [自选]`
- `💰 虚拟货币 [自选]`
- `🏦 美国银行 [自选]`
- `📈 美股 [自选]`
- `📺 YouTube [自选]`
- `🎬 流媒体 [自选]`
- `💬 Telegram [自选]`
- `🚀 默认代理 [自选]`

These are policy groups. They do not contain the service rules themselves.

## 4. Egress groups

### Regional system groups

- `🇺🇸 美国 [系统]`
- `🇯🇵 日本 [系统]`
- `🇸🇬 新加坡 [系统]`
- `🇭🇰 香港 [系统]`
- `🇹🇼 台湾 [系统]`
- `🌍 其他地区 [系统]`

Regional groups may use `url-test` to select among nodes that belong to that region.

### General/system egress

- `♻️ 自动选择 [系统]`
- `🌐 全部节点 [系统]`

### Optional user-controlled egress

Conceptually Hrules supports:

- `🎯 固定节点 [自选]`
- `🏠 ISP / 住宅 [自选]`

The implementation must not assume that node names reliably reveal whether a proxy is ISP/residential. Users or a later Hrules customization mechanism must explicitly assign such egresses. v0.1 must validate how optional/empty groups are represented before publishing them.

## 5. AI three-level design

### Level A: independent service rulesets

Maintain independent canonical rules for at least:

- Claude
- OpenAI
- Gemini
- Perplexity
- Grok
- Copilot
- other AI services added later

### Level B: service policy

Default mapping:

```text
Claude ──┐
         ├──> 🔐 Claude / OpenAI [自选]
OpenAI ──┘

Gemini ──────┐
Perplexity ──┤
Grok ────────┼──> 🤖 AI 服务 [自选]
Copilot ─────┤
Other AI ────┘
```

`🤖 AI 服务` may expose `🔐 Claude / OpenAI` as a downstream choice, allowing a user to intentionally reuse one common AI egress while preserving independent Claude/OpenAI rulesets.

### Level C: egress choice

`🔐 Claude / OpenAI` should be able to choose among appropriate regional groups, manual/fixed egress, optional ISP/residential egress, and all nodes.

It must **not** mean:

- Claude/OpenAI must use US;
- Claude/OpenAI must use residential IP;
- Claude/OpenAI must use static IP;
- Hrules can prevent account restrictions.

Its purpose is to make routing explicit, predictable, and user-controlled.

## 6. Egress-sensitive services

Hrules treats these as egress-sensitive from a routing perspective:

- Claude / OpenAI
- cryptocurrency services
- US banking
- US brokerage / stock-account services

Definition:

> Egress-sensitive means Hrules should avoid changing the effective egress without the user's intentional policy choice.

This is not an assertion that any particular IP type prevents service restrictions.

### Cryptocurrency

Expose one `💰 虚拟货币` group in v0.1 while keeping exchange-specific rule modules independently maintainable where practical. Do not force US routing because platform availability and user requirements differ by service and jurisdiction.

### US banking

`🏦 美国银行` should emphasize explicit user-controlled US, fixed-node, and optional ISP/residential choices. A normal stable US airport node remains a valid option.

### US stocks / brokerage

`📈 美股` should similarly support stable user-selected US/fixed/ISP-residential paths without requiring any one IP type. Brokerage/account traffic and general market-data rules should remain separable internally so they can be split later if needed.

## 7. Ordinary-service behavior

YouTube, streaming, Telegram and general traffic can prioritize usability and latency more aggressively than egress-sensitive services.

A global `♻️ 自动选择` group is appropriate as an option for ordinary traffic. It should not silently become the only path for sensitive-service groups.

## 8. Rule-order baseline

The first implementation should validate this order rather than blindly copy another configuration:

```text
1. Hrules explicit overrides / exceptions
2. private / LAN direct
3. reject / ads
4. sensitive service rules
   - Claude
   - OpenAI
   - crypto
   - US banking
   - US stocks / brokerage
5. ordinary service rules
   - other AI
   - YouTube
   - streaming
   - Telegram
   - platform/ecosystem services
6. CN domain direct
7. CN IP direct
8. MATCH -> 🚀 默认代理
```

The exact ordering must be covered by conflict tests because first-match behavior means overlapping rules can change the effective egress.

## 9. Regional-group implementation

Current community Mihomo configurations commonly use a hierarchy where service groups select regional groups, and regional groups use `url-test` plus name filters to select nodes. This is a useful pattern for Hrules, but Hrules must improve failure handling when a subscription has no nodes matching a region.

Requirements:

- regional regex must support common Chinese/English/flag naming;
- subscription metadata nodes such as expiry/traffic notices must be excluded where possible;
- no-match behavior must be tested;
- region groups should not depend on one airport's naming convention;
- manual access to actual nodes must remain possible.

## 10. Rule-provider architecture

Canonical Hrules service definitions remain independent even if the Mihomo output later combines or compiles them for performance.

Example conceptual mapping:

```yaml
rules:
  - RULE-SET,claude,🔐 Claude / OpenAI [自选]
  - RULE-SET,openai,🔐 Claude / OpenAI [自选]
  - RULE-SET,gemini,🤖 AI 服务 [自选]
  - RULE-SET,perplexity,🤖 AI 服务 [自选]
  - RULE-SET,crypto,💰 虚拟货币 [自选]
  - RULE-SET,us-banking,🏦 美国银行 [自选]
  - RULE-SET,us-stocks,📈 美股 [自选]
  - RULE-SET,youtube,📺 YouTube [自选]
  - RULE-SET,telegram,💬 Telegram [自选]
  - MATCH,🚀 默认代理 [自选]
```

This is architecture documentation, not yet a release configuration.

## 11. Validation requirements

Before v0.1 is public, tests must cover at least:

- configuration parses in current Mihomo;
- configuration works with a normal airport subscription and no custom ISP/fixed node;
- a subscription missing one or more regional node types does not break the config;
- Claude and OpenAI independently hit `🔐 Claude / OpenAI`;
- Gemini/other AI hit `🤖 AI 服务`;
- representative crypto domains hit `💰 虚拟货币`;
- representative US banking domains hit `🏦 美国银行`;
- representative brokerage domains hit `📈 美股`;
- YouTube hits its own group;
- representative CN domains/IPs are direct;
- unknown foreign traffic reaches `🚀 默认代理`;
- rule overlaps are detected before publication;
- optional ISP/residential support cannot break ordinary users;
- user-selected service policy persists where supported by the client.

## 12. Research observations used for this design

A reviewed current Mihomo configuration uses service groups selecting regional groups and regional `url-test` groups built with filters; its rules place service-specific sets before CN domain/IP direct and finish with `MATCH`. Another reviewed Clash/Mihomo script keeps OpenAI and Claude as independent rule providers and independent service groups, while exposing both regional automatic and regional manual groups. These patterns support Hrules' separation of service identity, service policy, and regional/node egress, but Hrules will not copy their rule data or topology verbatim.

## 13. Next implementation decisions

Before generating the first YAML, Hrules Core still needs to finalize:

- canonical source schema and provenance/license registry;
- exact v0.1 rule-source selection for Claude/OpenAI/AI/crypto/banking/brokerage;
- regional regex and no-match fallback behavior;
- safe representation of optional `固定节点` and `ISP / 住宅` groups;
- whether the Mihomo public artifact uses YAML/classical providers or generated MRS where appropriate;
- DNS/TUN defaults as a separate decision from routing policy;
- automated conflict and representative-routing test format.
