---
name: "cci-validate-character-mat-slot-names"
description: Validate CINEV character material slot names.
activation-check: normal
---

# cci-validate-character-mat-slot-names

## Step 0: Activation Check

- Continue only when the request explicitly matches `cci-validate-character-mat-slot-names` and its Unreal Engine responsibility.
- Confirm the target UE project, selected asset or input path, expected output, and whether the task may mutate assets.
- If target, scope, or destructive intent is unclear, ask before running scripts or editing files.
- Stop for non-Unreal, generic coding, or unrelated asset questions.
- Do not read skill-local references, run scripts, or follow later steps until this check passes.


Validate material slot names on character SkeletalMesh assets referenced in a DataTable.

## Skill-owned standards

Read `references/CINEV-CHARACTER-ASSET-NAMING.md` only when validating character asset, material, mesh, or texture names.

## Purpose

Two-step workflow for validating character material slot names:

1. **Export** (inside UE Editor) - Python script reads a DataTable, loads referenced SkeletalMesh assets, extracts material slot names, and validates against required slots
2. **Analyze** - The agent reads the JSON and provides a structured validation report

Ensures that all character meshes have required material slots (e.g., `Body_MTL`) for consistent post-processing and rendering pipelines.

---

## Usage

### One-Step (recommended)

Select a character DataTable in the Content Browser, then run:

```
/cci-validate-character-mat-slot-names --export
```

This remotely executes the export script in UE Editor and immediately analyzes the result.

### Manual Two-Step

#### Step 1: Export from UE Editor

Option A - Remote execution from terminal:
```bash
python "${CLAUDE_SKILL_DIR}/run_in_editor.py" "${CLAUDE_SKILL_DIR}/export_character_mat_slot_data.py"
```

Option B - Paste in UE Python console:
```python
exec(open(r"${CLAUDE_SKILL_DIR}/export_character_mat_slot_data.py").read())
```

JSON is saved to `.agent-local/private/unreal/character-mat-slot-validate/{name}.json`.

#### Step 2: Analyze

```
/cci-validate-character-mat-slot-names DT_Characters    # Analyze specific export
/cci-validate-character-mat-slot-names                   # List available exports
```

---

## Configuration

Edit `required_slots.json` to customize which material slots are required:

```json
{
  "required_slots": ["Body_MTL"]
}
```

---

## JSON Schema

```json
{
  "name": "DT_Name",
  "path": "/Game/.../DT_Name",
  "exported_at": "ISO 8601",
  "columns": ["---", "SkeletalMesh", "..."],
  "mesh_column": "SkeletalMesh",
  "row_count": 10,
  "validation": {
    "required_slots": ["Body_MTL"],
    "total": 10,
    "valid": 8,
    "invalid": 2,
    "results": [
      {
        "row_name": "Character01",
        "mesh_path": "/Game/.../SK_Character01",
        "material_slots": ["Body_MTL", "Hair_MTL", "Eye_MTL"],
        "missing_slots": [],
        "valid": true
      }
    ]
  }
}
```

---

## Files

- `export_character_mat_slot_data.py` - UE Editor script that exports DataTable mesh data and validates material slots
- `run_in_editor.py` - Remote execution bridge (verbatim copy from ue-analyze-material)
- `required_slots.json` - Required material slot names configuration
- `SKILL.md` - This documentation

---

## Related Files

- Skill: `skills/cci-validate-character-mat-slot-names/SKILL.md`
- Output: `.agent-local/private/unreal/character-mat-slot-validate/`
