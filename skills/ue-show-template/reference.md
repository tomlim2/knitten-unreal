# ue-show-template Reference

UE Python script patterns, remote sender details, command template, SKILL.md template, creation checklist, and reference implementation.

---

## Pattern: UE Python Script (`export_{noun}_data.py`)

### Structure (in order)

1. **Docstring** - what it does, how to run, supported types, output path
2. **Imports** - always: `unreal`, `json`, `os`, `datetime`
3. **Enum maps** - `dict[int, str]` for each relevant UE enum
4. **`get_enum_name()`** - shared resolver (handles int, UE enum objects, repr strings)
5. **Type extractors** - one `extract_{type}(asset)` per supported asset type
6. **Shared helpers** - `_make_base_dict()`, `save_json()`
7. **`main()`** - get selection, isinstance dispatch, log summary
8. **`main()` call** - at module level

### Key Patterns

**Property access** - always wrap individually:
```python
try:
    data["properties"]["prop"] = asset.get_editor_property("prop")
except Exception:
    data["properties"]["prop"] = "Unknown"  # or None, [], etc.
```

**Type dispatch** - most-specific first:
```python
if isinstance(asset, unreal.MaterialInstanceConstant):  # subclass first
    ...
elif isinstance(asset, unreal.MaterialFunction):         # sibling types
    ...
elif isinstance(asset, unreal.Material):                 # parent class last
    ...
else:
    unreal.log_warning(f"[{SkillTag}] Skipping '{asset.get_name()}' - (type: {asset.get_class().get_name()})")
```

**Non-exposed properties** - use ObjectIterator:
```python
asset_path = asset.get_path_name()
children = []
for obj in unreal.ObjectIterator(unreal.SomeBaseClass):
    if obj.get_outer() and obj.get_outer().get_path_name() == asset_path:
        children.append(obj)
```

**Save path:**
```python
output_dir = os.path.join(os.path.expanduser("~"), ".agent-local", "private", "unreal", "{subdirectory}")
```

### JSON Output Schema (base)

Every export shares this base:
```json
{
  "name": "asset.get_name()",
  "path": "asset.get_path_name()",
  "type": "AssetType string",
  "exported_at": "ISO 8601",
  "properties": {}
}
```

Add asset-specific fields as needed. Delete irrelevant ones per type.

---

## Pattern: Remote Sender (`run_in_editor.py`)

**Copy verbatim** from `ue-analyze-material/run_in_editor.py`. Only update `_UE_PYTHON_PLUGIN_PATHS` if engine path differs.

Key: send **file path** to UE (not file content) via `MODE_EXEC_FILE`.

---

## Pattern: Command (`unreal-{verb}-{noun}.md`)

### Frontmatter
```yaml
---
allowed-tools: Read, Glob, Task, Grep, Bash(python:*)
description: {description}
argument-hint: "[{noun}_name | --export]"
---
```

### Three behaviors

1. **`--export`**: Run `python run_in_editor.py export_{noun}_data.py`, then analyze result
2. **No argument**: List available JSONs in output dir, stop
3. **Named argument**: Read `.agent-local/private/unreal/{subdirectory}/{arg}.json`, analyze

### Analysis sections (customize per asset type)

1. Overview (name, path, type, timestamp)
2. Properties
3-N. Asset-specific sections
N+1. Observations (issues, complexity, suggestions)

---

## Pattern: SKILL.md

Sections in order:
1. Title + version
2. Changelog
3. Purpose
4. Usage (one-step `--export` + manual two-step)
5. Remote Execution reference
6. JSON Schema
7. Related Files

---

## Checklist: Creating a New Skill

```
[ ] Define: verb, noun, supported UE asset types, output JSON schema
[ ] Create: skills/ue-{verb}-{noun}/
[ ] Write:  SKILL.md
[ ] Write:  export_{noun}_data.py
    [ ] Enum maps for relevant enums
    [ ] extract_*() for each asset type
    [ ] _make_base_dict() with correct schema
    [ ] save_json() with correct subdirectory
    [ ] main() with isinstance dispatch
[ ] Copy:   run_in_editor.py (verbatim)
[ ] Write:  commands/ue-{verb}-{noun}.md
    [ ] --export triggers remote execution
    [ ] No-arg lists available exports
    [ ] Named arg reads and analyzes JSON
[ ] Test:   Select asset → /ue-{verb}-{noun} --export → verify JSON → verify analysis
```

---

## Reference Implementation

- `skills/ue-analyze-material/` - the original skill this pattern was extracted from

---

## Related Files

- Generator workflow: skill creation workflow in the Knitten core plugin
- Reference skill: `skills/ue-analyze-material/`
- Shared sender: `skills/ue-analyze-material/run_in_editor.py`
