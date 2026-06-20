---
name: "ue-show-template"
description: Reference template for UE Editor skills.
domains: unreal
repo-keys: anju,mega-melange
languages: python
task-types: implementation
context-profile: unreal-engine
exclude-when: rust,web,obsidian
activation-check: normal
---

# ue-show-template

## Step 0: Activation Check

- Continue only when the request explicitly matches `ue-show-template` and its Unreal Engine responsibility.
- Confirm the target UE project, selected asset or input path, expected output, and whether the task may mutate assets.
- If target, scope, or destructive intent is unclear, ask before running scripts or editing files.
- Stop for non-Unreal, generic coding, or unrelated asset questions.
- Do not read skill-local references, run scripts, or follow later steps until this check passes.


Pattern reference for creating UE Editor skills that follow the proven `ue-analyze-material` architecture.

## Purpose

This is not a runnable skill. It's a **pattern specification** that the `/ue-make-skill` command reads to generate new UE Editor skills with consistent architecture.

## Architecture: 3-Part Structure

```
skills/ue-{verb}-{noun}/
├── SKILL.md                      # Metadata + documentation
├── export_{noun}_data.py         # Runs inside UE Editor
└── run_in_editor.py              # Shared remote execution sender (copy verbatim)

commands/
└── unreal-{verb}-{noun}.md       # Claude Code command interface

.agent-local/private/unreal/
└── {noun}-{verb}/                # JSON output directory (auto-created)
```

**Flow:** User selects asset in Content Browser → Command triggers `run_in_editor.py` → UE Editor runs `export_{noun}_data.py` → JSON saved → Command reads JSON → Claude analyzes

## Placeholders

| Placeholder | Example | Rules |
|---|---|---|
| `{verb}` | `analyze` | Present tense, lowercase, kebab-case in paths |
| `{noun}` | `material` | Singular, lowercase |
| `{Noun}` | `Material` | Capitalized for display |
| `{ASSET_TYPES}` | `Material, MaterialInstanceConstant, MaterialFunction` | UE class names |
| `{SkillTag}` | `MaterialAnalyze` | PascalCase for `[log prefix]` |
| `{subdirectory}` | `material-analyze` | `{noun}-{verb}` for output dir |
| `{description}` | `Export and analyze UE material node graphs` | One line |

## Additional Resources

For UE Python script patterns, remote sender details, command patterns, SKILL.md template, creation checklist, and reference implementation, see [reference.md](reference.md).
