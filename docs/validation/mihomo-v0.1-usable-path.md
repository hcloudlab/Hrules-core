# Mihomo v0.1 complete usable path

Status: automated acceptance candidate

## User path

1. Export or obtain an existing Mihomo/Clash YAML that contains real proxies.
2. Run:
   `python generators/build_mihomo_from_config.py source.yaml --include-research --out hrules-mihomo.yaml`
3. Hrules preserves the source proxies and ordinary non-routing runtime settings.
4. Hrules deliberately replaces routing-owned `proxy-groups`, `rules`, and legacy `rule-providers` with its validated topology and canonical routing behavior.
5. Validate the generated file with the actual Mihomo core:
   `mihomo -t -f hrules-mihomo.yaml`
6. Import the resulting YAML into a Mihomo-family client such as Clash Verge Rev and perform real-client connection-page verification.

## Safety boundary

The transformer never edits the source file in place. It fails if there are no proxies, proxy names are missing, or proxy names are duplicated.

This automated path proves configuration transformation and real-core syntax acceptance. It does **not** by itself prove Clash Verge Rev GUI import/runtime behavior on a user's machine. That remains the final real-client acceptance step before calling Mihomo v0.1 fully user-validated.

Blocking remains research-only and is included in this proof path only when `--include-research` is explicitly supplied.
