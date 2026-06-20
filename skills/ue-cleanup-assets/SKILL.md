---
name: "ue-cleanup-assets"
description: Find and delete unused Unreal assets.
domains: unreal
repo-keys: anju,mega-melange
languages: python
task-types: implementation
context-profile: unreal-engine
exclude-when: rust,web,obsidian
disable-model-invocation: false
activation-check: normal
---

# ue-cleanup-assets

## Step 0: Activation Check

- Continue only when the request explicitly matches `ue-cleanup-assets` and its Unreal Engine responsibility.
- Confirm the target UE project, selected asset or input path, expected output, and whether the task may mutate assets.
- If target, scope, or destructive intent is unclear, ask before running scripts or editing files.
- Stop for non-Unreal, generic coding, or unrelated asset questions.
- Do not read skill-local references, run scripts, or follow later steps until this check passes.


Find and delete unused (unreferenced) assets in UE Editor.

## Purpose

Two-phase workflow for cleaning up unreferenced assets in Unreal Engine:

1. **Scan** (safe) — Check selected assets for references, save results to JSON
2. **Delete** (destructive) — Read scan results and delete confirmed unused assets

The original script combined both phases. This skill separates them for safety: you always review the scan results before any deletion happens.

## Usage

### Phase 1: Scan for unused assets

Select assets in UE Content Browser, then:

```
/ue-cleanup-assets --scan
```

Executes `find_unused_assets.py` in UE Editor via remote execution. Results saved to:
`.agent-local/private/unreal/assets-cleanup/scan_YYYYMMDD_HHMMSS.json`

### Phase 2: Review and delete

```
/ue-cleanup-assets                    # List available scan files
/ue-cleanup-assets <scan_filename>    # Review a specific scan
/ue-cleanup-assets --delete <file>    # Delete unused assets from scan (requires confirmation)
```

## JSON Schema

```json
{
  "scanned_at": "2026-02-10T14:30:00",
  "total_scanned": 10,
  "unused_count": 3,
  "unused_assets": [
    { "name": "T_Unused", "path": "/Game/Textures/T_Unused", "type": "Texture2D" }
  ],
  "referenced_assets": [
    { "name": "T_Used", "path": "/Game/Textures/T_Used", "type": "Texture2D", "referencer_count": 2 }
  ]
}
```

## Remote Execution

Uses `run_in_editor.py` (same as ue-analyze-material) to send Python scripts to UE Editor via Python Remote Execution protocol.

## Files

- `find_unused_assets.py` - Phase 1: Scan selected assets for references (UE Editor script)
- `delete_unused_assets.py` - Phase 2: Delete assets listed in scan JSON (UE Editor script)
- `run_in_editor.py` - Remote execution bridge (copied from ue-analyze-material)

## Related Files

- Skill: `skills/ue-cleanup-assets/SKILL.md`
- Output: `.agent-local/private/unreal/assets-cleanup/`
- Original: `anju/python/asset_manager/find_no_reference_and_delete.py`
