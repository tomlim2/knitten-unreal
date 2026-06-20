---
name: "cci-rename-mat-slot"
description: Rename invalid CINEV material slots.
disable-model-invocation: false
activation-check: normal
---

# cci-rename-mat-slot

## Step 0: Activation Check

- Continue only when the request explicitly matches `cci-rename-mat-slot` and its Unreal Engine responsibility.
- Confirm the target UE project, selected asset or input path, expected output, and whether the task may mutate assets.
- If target, scope, or destructive intent is unclear, ask before running scripts or editing files.
- Stop for non-Unreal, generic coding, or unrelated asset questions.
- Do not read skill-local references, run scripts, or follow later steps until this check passes.


Rename material slot names on character SkeletalMesh assets based on validation results.

## Purpose

Automated fix for invalid material slot names discovered by `cci-validate-character-mat-slot-names`. Reads validation JSON, finds meshes with mismatched slot names (e.g., `Body_MTL1`, `Body_MTL2`), and renames them to the expected names (e.g., `Body_MTL`).

Works with any character mesh type: Head, Hair, Body.

## Usage

### One-Step (recommended)

First run validation, then rename:

```
/cci-validate-character-mat-slot-names
/cci-rename-mat-slot
```

### Manual

Remote execution from terminal:
```bash
python "${CLAUDE_SKILL_DIR}/run_in_editor.py" "${CLAUDE_SKILL_DIR}/rename_mat_slots.py"
```

## Matching Algorithm

For each missing slot (e.g., `Body_MTL`):
1. Search existing slots for pattern: `{missing_slot}` + single digit (1-9)
2. Candidates: `Body_MTL1`, `Body_MTL2`, and other numbered variants.
3. Pick shortest name (closest match)
4. If no match found, skip with warning

## JSON Schema

```json
{
  "source": "DT_LookDevHead",
  "source_file": "DT_LookDevHead.json",
  "executed_at": "ISO 8601",
  "total_meshes": 5,
  "renamed": 4,
  "failed": 1,
  "results": [
    {
      "mesh_path": "/Game/.../Rosee_head",
      "renames": [
        { "from": "Body_MTL1", "to": "Body_MTL" }
      ],
      "skipped": [],
      "error": null
    }
  ]
}
```

## Files

- `rename_mat_slots.py` - UE Editor script that renames material slots
- `run_in_editor.py` - Remote execution bridge (verbatim copy)
- `SKILL.md` - This documentation

## Related Files

- Validation skill: `skills/cci-validate-character-mat-slot-names/`
- Skill: `skills/cci-rename-mat-slot/SKILL.md`
- Output: `.agent-local/private/unreal/mat-slot-rename/`
