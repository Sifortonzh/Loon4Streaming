# Loon4Streaming · Generated from the shared Surge template

[中文说明](./README_ZH.md) | [Surge source repository](https://github.com/Sifortonzh/Config4Streaming)

## Import

Download [Loon4Streaming_rebuilt.conf](https://raw.githubusercontent.com/Sifortonzh/Loon4Streaming/main/Loon4Streaming_rebuilt.conf) and import it as a **new Loon profile** on iPad, keeping the previous profile available for rollback.

1. Retain your nodes/subscriptions if the import UI offers that option, or add the provider's **Loon subscription** to the new profile. A complete Surge profile is not a native Loon node subscription.
2. MESL/SNTP example.com entries are disabled placeholders. Replace and enable them locally, or retain existing subscriptions. Never commit private URLs.
3. Update subscriptions. Check Sub-ALL and region filters. Zero in Sub-ALL means the subscription format/enabled state must be fixed before changing routing rules; zero in one region may mean no such nodes exist.
4. Select **rule mode**, temporarily disable other rule/plugin overrides when diagnosing, then reconnect.
5. Apple and WeChat default to DIRECT; PikPak defaults to Singapore; Bilibili includes domestic and Bstation international domains. Other group choices, order and icons follow the public Surge template.
6. Verify the matched policy and actual egress in Loon request logs and test playback. Latency tests do not establish streaming unlock.

The approximately 4 MB profile uses a local rule snapshot and may take time to load initially. It contains no real subscription, certificate, plugins, scripts or MITM. Existing historical .conf/.lcf files remain untouched; **rebuilt is the current entry point**.

## Configuration differences addressed

These are confirmed configuration differences, not a completed diagnosis of a particular failed request on the user's iPad.

- Old filters explicitly bound to PAOPAO/Mitce aliases could miss nodes imported under another subscription name. New NameRegex filters include all nodes and support compact labels such as HK01, SGP05, PH01 and SK01, traditional Chinese region names and common flags. Traffic/expiration notices are excluded; Taiwan is not inferred from the China flag alone.
- Loon gives domain rules precedence over IP rules and local rules precedence over plugin/subscription rules. Rules are downloaded and expanded in Surge template order into one local [Rule] section. This avoids cross-source priority changes. **Loon's native domain-before-IP behavior remains different from Surge.**
- Surge smart becomes native Loon url-test: lowest measured latency, not the same smart algorithm and not an unlock test.
- icon-url becomes img-url; group order is retained. New groups stay at the end.
- macOS/Android process matching is omitted for iPad. Unknown rule types stop generation instead of being silently ignored.
- Apple's split domain list is now explicitly referenced in the shared Surge template; DOMAIN-SET becomes native Loon DOMAIN / DOMAIN-SUFFIX entries.
- UDP-unsupported traffic is rejected rather than silently sent direct. Loon-native DNS interception and encrypted DNS are configured. HTTP-visible rules such as USER-AGENT retain their native HTTPS visibility limitations.

References: [rule priority](https://nsloon.app/en/docs/Rule/), [node filters](https://nsloon.app/en/docs/Node/nodefilter/), [subscription formats](https://nsloon.app/en/docs/Node/subscription/), [policy groups](https://nsloon.app/en/docs/Policy/policygroup/).

## One-click updates

Double-click [tools/sync.command](./tools/sync.command) on Mac. Preview and validate, then choose 🔄 1 to generate or 🚀 2 to generate and push main over SSH.

The source defaults to the adjacent Config4Streaming/templates/Surge.shared.conf. Only public settings are read. Run the existing Surge sync first after editing MESL/SNTP, then run Loon sync. The two publishing steps remain independent. iPad changes are not automatically uploaded or merged back into Surge.

- python3 tools/sync_from_surge.py previews; --apply writes; --apply --publish publishes.
- --refresh refreshes public resources; --offline uses cache only and cannot publish.
- --source selects another sanitized shared template. Private subscription/certificate input is rejected.
- --private-profile /path/to/old-loon.conf copies ONLY local/remote node sections into ignored .loon-sync/Loon4Streaming.private.conf for personal import. No external subscription converter is contacted.
- Ignored .loon-sync/ stores caches/backups. Prior generated files are backed up. Manual edits to a previously generated file stop replacement; merge those edits into the source first.
- Source URLs, counts and hashes are recorded in [validation-report.json](./validation-report.json). Rule snapshots require regeneration and reimport/profile refresh on iPad when sources change; this is not automatic background iPad sync.
- Only named public artifacts are staged; unrelated local historical deletions are excluded. Push failure leaves local generated files/backups available for retry.

Requires Python 3 and Git. Tests: python3 -m unittest discover -s tools -p 'test_*.py'. Import, subscription parsing, filter counts and playback still require on-device verification.

## Attribution

Policies: [Config4Streaming](https://github.com/Sifortonzh/Config4Streaming). Rule sources: BlackMatrix7 ios_rule_script, AWAvenue, Semporia and Sifortonzh custom lists. Exact sources and hashes are recorded in the report. Icons retain their original Qure, Orz-3/mini, Semporia and other author URLs. Respect upstream licenses and attribution when redistributing snapshots.
