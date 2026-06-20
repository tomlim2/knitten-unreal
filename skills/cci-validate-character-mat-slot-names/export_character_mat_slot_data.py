"""
Export character DataTable material slot data for validation.

Run inside UE Editor Python console:
    exec(open(__import__("os").path.expanduser(r"~\\.agent-local\\skills\\cci-validate-character-mat-slot-names\\export_character_mat_slot_data.py")).read())

Selects a DataTable in Content Browser, extracts SkeletalMesh references,
loads each mesh to get material slot names, and validates against required slots.

Output: .agent-local/private/unreal/character-mat-slot-validate/{name}.json
"""

import unreal
import json
import os
import re
from datetime import datetime


LOG_TAG = "CharMatSlotValidate"


# ---------------------------------------------------------------------------
# Asset reference parsing
# ---------------------------------------------------------------------------

def parse_asset_reference(raw):
    """Extract clean asset path from DataTable JSON value.

    Handles formats like:
        /Game/Path/SK_Mesh.SK_Mesh
        /Game/Path/SK_Mesh
        None
    """
    if not raw or not isinstance(raw, str):
        return None
    raw = raw.strip()
    if raw in ("", "None", "null"):
        return None

    # Remove .ObjectName suffix: /Game/Path/Mesh.Mesh -> /Game/Path/Mesh
    if '.' in raw:
        raw = raw.rsplit('.', 1)[0]

    if raw.startswith('/Game/') or raw.startswith('/Script/'):
        return raw

    return None


# ---------------------------------------------------------------------------
# DataTable JSON extraction
# ---------------------------------------------------------------------------

def extract_datatable_json(data_table):
    """Export DataTable to JSON using DataTableFunctionLibrary.

    Returns: list of row dicts, or None on failure.
    """
    try:
        json_str = unreal.DataTableFunctionLibrary.export_data_table_to_json_string(
            data_table
        )
    except Exception as e:
        unreal.log_error(f"[{LOG_TAG}] export_data_table_to_json_string failed: {e}")
        return None

    if not json_str:
        unreal.log_error(f"[{LOG_TAG}] Empty JSON from DataTable export")
        return None

    try:
        rows = json.loads(json_str)
    except json.JSONDecodeError as e:
        unreal.log_error(f"[{LOG_TAG}] JSON parse error: {e}")
        return None

    return rows


def get_column_names(data_table):
    """Get DataTable column names via DataTableFunctionLibrary."""
    try:
        return [
            str(c) for c in
            unreal.DataTableFunctionLibrary.get_data_table_column_names(data_table)
        ]
    except Exception:
        return []


def find_mesh_column(columns, rows):
    """Find the column name that contains SkeletalMesh references."""
    # Check by column name
    for col in columns:
        col_lower = col.lower()
        if "skeletalmesh" in col_lower or "skeletal_mesh" in col_lower:
            return col
        if col_lower == "mesh":
            return col

    # Check by data content
    for col in columns:
        if col == "Name":
            continue
        for row in rows[:5]:
            val = str(row.get(col, ""))
            if "/Game/" in val and ("Mesh" in val or "SK_" in val or "head" in val.lower()):
                return col

    return None


# ---------------------------------------------------------------------------
# Material slot extraction
# ---------------------------------------------------------------------------

def get_material_slots(mesh_path):
    """Load a SkeletalMesh and return its material slot names."""
    mesh = unreal.EditorAssetLibrary.load_asset(mesh_path)
    if mesh is None:
        return None, "Failed to load asset"

    if not isinstance(mesh, unreal.SkeletalMesh):
        return None, f"Not a SkeletalMesh (type: {mesh.get_class().get_name()})"

    slot_names = []
    try:
        materials = mesh.get_editor_property("materials")
        for mat_slot in materials:
            name = str(mat_slot.get_editor_property("material_slot_name"))
            slot_names.append(name)
    except Exception as e:
        return None, f"Error reading materials: {e}"

    return slot_names, None


# ---------------------------------------------------------------------------
# Required slots config
# ---------------------------------------------------------------------------

def load_required_slots():
    """Load required slot names from config file."""
    config_dir = os.path.join(
        __import__("os").path.expanduser("~"), ".agent-local", "skills",
        "cci-validate-character-mat-slot-names"
    )
    config_path = os.path.join(config_dir, "required_slots.json")

    if not os.path.isfile(config_path):
        unreal.log_warning(
            f"[{LOG_TAG}] Config not found: {config_path}, "
            f"using default ['Body_MTL']"
        )
        return ["Body_MTL"]

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    return config.get("required_slots", ["Body_MTL"])


def validate_slots(slot_names, required_slots):
    """Check which required slots are missing."""
    return [s for s in required_slots if s not in slot_names]


# ---------------------------------------------------------------------------
# JSON output
# ---------------------------------------------------------------------------

def save_json(data, name):
    """Save result JSON to output directory."""
    output_dir = os.path.join(
        __import__("os").path.expanduser("~"), ".agent-local", "private", "unreal",
        "character-mat-slot-validate"
    )
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{name}.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    unreal.log(f"[{LOG_TAG}] Saved: {output_path}")
    return output_path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

DEFAULT_DATATABLE = "/Game/Character/Anime/_LookDev/DataTable/DT_LookDevHead"


def main():
    selected = unreal.EditorUtilityLibrary.get_selected_assets()

    if not selected:
        unreal.log(f"[{LOG_TAG}] No selection. Loading default: {DEFAULT_DATATABLE}")
        dt = unreal.EditorAssetLibrary.load_asset(DEFAULT_DATATABLE)
        if dt is None:
            unreal.log_error(f"[{LOG_TAG}] Failed to load: {DEFAULT_DATATABLE}")
            return
        selected = [dt]

    # Load required slots once
    required_slots = load_required_slots()
    unreal.log(f"[{LOG_TAG}] Required slots: {required_slots}")

    processed = 0
    for asset in selected:
        if not isinstance(asset, unreal.DataTable):
            unreal.log_warning(
                f"[{LOG_TAG}] Skipping '{asset.get_name()}' - "
                f"not a DataTable (type: {asset.get_class().get_name()})"
            )
            continue

        dt_name = asset.get_name()
        dt_path = asset.get_path_name()
        unreal.log(f"[{LOG_TAG}] Processing DataTable: {dt_name}")

        # Get column names
        columns = get_column_names(asset)
        unreal.log(f"[{LOG_TAG}] Columns: {columns}")

        # Extract rows via JSON
        rows = extract_datatable_json(asset)
        if not rows:
            continue

        unreal.log(f"[{LOG_TAG}] Extracted {len(rows)} rows")

        # Find SkeletalMesh column
        mesh_col = find_mesh_column(columns, rows)
        if not mesh_col:
            unreal.log_error(
                f"[{LOG_TAG}] No SkeletalMesh column found. "
                f"Columns: {columns}"
            )
            continue

        unreal.log(f"[{LOG_TAG}] Using column: '{mesh_col}'")

        # Process each row
        results = []
        valid_count = 0
        invalid_count = 0

        for row in rows:
            row_name = row.get("Name", "Unknown")
            raw_mesh = row.get(mesh_col, "")
            mesh_path = parse_asset_reference(raw_mesh)

            result = {
                "row_name": row_name,
                "mesh_path": mesh_path,
                "material_slots": [],
                "missing_slots": [],
                "valid": False,
            }

            if not mesh_path:
                result["error"] = "No mesh path"
                invalid_count += 1
                results.append(result)
                continue

            slot_names, error = get_material_slots(mesh_path)
            if error:
                result["error"] = error
                invalid_count += 1
                results.append(result)
                continue

            result["material_slots"] = slot_names
            missing = validate_slots(slot_names, required_slots)
            result["missing_slots"] = missing
            result["valid"] = len(missing) == 0

            if result["valid"]:
                valid_count += 1
            else:
                invalid_count += 1

            results.append(result)

        # Build output
        data = {
            "name": dt_name,
            "path": dt_path,
            "exported_at": datetime.now().isoformat(timespec="seconds"),
            "columns": columns,
            "mesh_column": mesh_col,
            "row_count": len(rows),
            "validation": {
                "required_slots": required_slots,
                "total": len(results),
                "valid": valid_count,
                "invalid": invalid_count,
                "results": results,
            },
        }

        save_json(data, dt_name)
        unreal.log(
            f"[{LOG_TAG}] DataTable '{dt_name}' - "
            f"{len(rows)} rows, {valid_count} valid, "
            f"{invalid_count} invalid"
        )
        processed += 1

    if processed == 0:
        unreal.log_warning(f"[{LOG_TAG}] No DataTables found in selection.")
    else:
        unreal.log(f"[{LOG_TAG}] Done. Exported {processed} DataTable(s).")


main()
