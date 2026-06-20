# Knitten Unreal

Knitten Unreal is a private Knitten payload plugin for Unreal Engine skills.

It contains concrete UE workflow skills under `skills/`, including material
analysis, redirector checks, unused asset cleanup, Nanite/translucent fixes,
sprite sheet generation, asset naming validation, and CINEV character helpers.

## Relationship

| Repository | Use it for |
|------------|------------|
| `knitten` | Shared Agent Hub routing, output paths, workflow contracts, and boundary rules. |
| `knitten-all-skills` | General non-Shotloom private skills. |
| `knitten-sl` | Shotloom-specific skills. |
| `knitten-unreal` | Unreal Engine and UE Editor workflow skills. |

## Local Install

Refresh the local plugin copy:

```bash
node scripts/materialize-local-plugin.mjs
node scripts/doctor.mjs
```

The materialize script copies this checkout into
`<home-directory>/plugins/knitten-unreal` and upserts the
`knitten-unreal` entry in `<home-directory>/.agents/plugins/marketplace.json`.

Restart Codex after refreshing plugin installations. Existing sessions may keep
the old skill list until a new session starts.

## Validation

```bash
node scripts/validate-routing.mjs
node scripts/validate-boundary.mjs --warn-only
node scripts/doctor.mjs
```

Strict payload boundary validation may report historical docs warnings when docs
exist. This repository is intended to keep active runtime material under
`skills/`, `scripts/`, and `.codex-plugin/`.
