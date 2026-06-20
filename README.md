# Knitten Unreal

Knitten Unreal is an MIT-licensed fresh-start Knitten payload plugin for future
Unreal Engine and UE Editor workflow skills.

The previous Unreal-specific skill payload has moved back into
`knitten-all-skills` (KAS). This repository is intentionally kept as a clean
placeholder until the dedicated Unreal payload is redesigned.

Repository: <https://github.com/tomlim2/knitten-unreal>

## Included Skills

None currently. Use KAS for the existing Unreal Engine and CINEV workflow
skills.

## Relationship

| Repository | Use it for |
|------------|------------|
| `knitten` | Shared Agent Hub routing, output paths, workflow contracts, and boundary rules. |
| `knitten-all-skills` | General non-Shotloom private skills, including the current Unreal Engine helpers. |
| `knitten-sl` | Shotloom-specific skills. |
| `knitten-unreal` | Fresh-start placeholder for a future redesigned Unreal payload. |

## Layout

For Unreal task defaults, read
[`references/unreal-llm-rules.md`](references/unreal-llm-rules.md) first. It is
the small text-only context file; do not load the full reference pack unless the
task needs deeper details.

| Path | Purpose |
|------|---------|
| `.codex-plugin/plugin.json` | Codex plugin manifest. |
| `references/` | Unreal MCP, UE 5.8 toolset, and PCG reference notes for future skill design. |
| `skills/` | Empty skill payload root kept for future Unreal skills. |
| `scripts/unreal/` | Reusable Unreal MCP and UE Python helper scripts for research and prototypes. |
| `scripts/materialize-local-plugin.mjs` | Copy this checkout into the local Codex plugin folder and update the marketplace entry. |
| `scripts/doctor.mjs` | Check source and installed plugin health. |
| `scripts/validate-routing.mjs` | Check skill activation-gate requirements. |
| `scripts/validate-boundary.mjs` | Delegate payload boundary validation to Knitten core. |

## Local Install

Refresh the local plugin copy:

```bash
node scripts/materialize-local-plugin.mjs
node scripts/doctor.mjs
```

The materialize script copies this checkout into
`<home-directory>/plugins/knitten-unreal` and upserts the `knitten-unreal`
entry in `<home-directory>/.agents/plugins/marketplace.json`.

The local marketplace should include Knitten core and any payload plugins you
want enabled. `knitten-unreal` is optional while it has no active skills:

```text
knitten@knitten-local
knitten-all-skills@knitten-local
knitten-sl@knitten-local
```

Restart Codex after refreshing plugin installations. Existing sessions may keep
the old skill list until a new session starts.

## Validation

```bash
python3 <plugin-creator>/scripts/validate_plugin.py .
node scripts/validate-routing.mjs
node scripts/validate-boundary.mjs --warn-only
node scripts/doctor.mjs
```

Expected state:

- plugin validation passes
- routing validation reports `0 skills`
- boundary validation reports no errors
- doctor reports source and copied plugin checks as OK

## License

MIT. See [LICENSE](LICENSE).
