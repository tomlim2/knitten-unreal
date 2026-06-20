# Knitten Unreal

Knitten Unreal is an MIT-licensed Knitten payload plugin for Unreal Engine and
UE Editor workflow skills.

It carries the Unreal-specific skill payload. The shared Knitten core plugin
still owns generic routing, output paths, workflow contracts, and payload
boundary validation.

Repository: <https://github.com/tomlim2/knitten-unreal>

## Included Skills

| Skill | Purpose |
|-------|---------|
| `cci-deploy-pmx-character` | Convert and deploy PMX characters into a UE/CINEV character workflow. |
| `cci-rename-mat-slot` | Rename invalid CINEV character material slots after validation. |
| `cci-validate-character-mat-slot-names` | Validate CINEV character SkeletalMesh material slot names. |
| `ue-analyze-material` | Export and analyze Unreal material node graphs. |
| `ue-check-redirectors` | Scan Unreal ObjectRedirector assets and report stale or broken redirectors. |
| `ue-cleanup-assets` | Scan and optionally delete unused Unreal assets with a review step. |
| `ue-fix-nanite-translucent` | Disable Nanite on meshes using translucent materials where needed. |
| `ue-generate-spritesheet` | Generate UE flipbook sprite sheets from image sequences. |
| `ue-show-template` | Reference template for creating UE Editor skills. |
| `ue-validate-asset-name` | Validate and fix Unreal asset names against naming conventions. |

Every skill has an activation gate so detailed instructions and scripts are
loaded only after the request clearly matches that skill.

## Relationship

| Repository | Use it for |
|------------|------------|
| `knitten` | Shared Agent Hub routing, output paths, workflow contracts, and boundary rules. |
| `knitten-all-skills` | General non-Shotloom private skills. |
| `knitten-sl` | Shotloom-specific skills. |
| `knitten-unreal` | Unreal Engine and UE Editor workflow skills. |

## Layout

| Path | Purpose |
|------|---------|
| `.codex-plugin/plugin.json` | Codex plugin manifest. |
| `skills/` | Unreal skill payload exposed by the plugin manifest. |
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
want enabled:

```text
knitten@knitten-local
knitten-all-skills@knitten-local
knitten-sl@knitten-local
knitten-unreal@knitten-local
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
- routing validation reports `10 skills`
- boundary validation reports no errors
- doctor reports source and copied plugin checks as OK

## License

MIT. See [LICENSE](LICENSE).
