"""
Rename material slots on character SkeletalMesh assets based on validation results.

Run inside UE Editor Python console:
    exec(open(__import__("os").path.expanduser(r"~\\.agent-local\\skills\\cci-rename-mat-slot\\rename_mat_slots.py")).read())

Reads the most recent validation JSON, finds meshes with invalid slot names,
and renames slots to match expected names (e.g., Body_MTL1 -> Body_MTL).

Output: .agent-local/private/unreal/mat-slot-rename/{source}.json
"""

import unreal
import json
import os
import re
from datetime import datetime


LOG_TAG = "CharMatSlotRename"


# ---------------------------------------------------------------------------
# Validation JSON loading
# ---------------------------------------------------------------------------

def get_latest_validation_json():
    """Find the most recent validation JSON file."""
    validate_dir = os.path.join(
        __import__("os").path.expanduser("~"), ".agent-local", "private", "unreal",
        "character-mat-slot-validate"
    )

    if not os.path.isdir(validate_dir):
        unreal.log_error(
            f"[{LOG_TAG}] Validation directory not found: {validate_dir}"
        )
        return None, None

    json_files = [
        f for f in os.listdir(validate_dir) if f.endswith(".json")
    ]

    if not json_files:
        unreal.log_error(f"[{LOG_TAG}] No validation JSON files found")
        return None, None

    # Sort by modification time, newest first
    json_files.sort(
        key=lambda f: os.path.getmtime(os.path.join(validate_dir, f)),
        reverse=True,
    )

    latest = json_files[0]
    path = os.path.join(validate_dir, latest)

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    unreal.log(f"[{LOG_TAG}] Loaded validation: {path}")
    return data, latest


def get_invalid_meshes(validation_data):
    """Extract unique mesh paths with missing slots from validation results."""
    results = validation_data.get("validation", {}).get("results", [])

    # Collect invalid entries, deduplicate by mesh_path
    mesh_map = {}
    for row in results:
        if row.get("valid", True):
            continue
        mesh_path = row.get("mesh_path")
        if not mesh_path:
            continue
        missing = row.get("missing_slots", [])
        if not missing:
            continue

        # Keep first occurrence (dedup by mesh_path)
        if mesh_path not in mesh_map:
            mesh_map[mesh_path] = {
                "mesh_path": mesh_path,
                "missing_slots": missing,
                "existing_slots": row.get("material_slots", []),
            }

    return list(mesh_map.values())


# ---------------------------------------------------------------------------
# Slot matching
# ---------------------------------------------------------------------------

def find_best_match(missing_slot, existing_slots):
    """Find the best existing slot name that matches the missing slot pattern.

    For missing_slot = "Body_MTL", looks for existing slots like
    "Body_MTL1", "Body_MTL2", etc. (missing_slot + single digit).

    Returns the shortest matching name, or None if no match found.
    """
    pattern = re.compile(r"^" + re.escape(missing_slot) + r"[1-9]$")
    candidates = [s for s in existing_slots if pattern.match(s)]

    if not candidates:
        return None

    # Pick shortest name (closest match)
    candidates.sort(key=len)
    return candidates[0]


# ---------------------------------------------------------------------------
# Rename execution
# ---------------------------------------------------------------------------

def rename_slots_on_mesh(mesh_path, missing_slots, existing_slots):
    """Load mesh, find matching slots, rename them, and save.

    Returns dict with rename results.
    """
    result = {
        "mesh_path": mesh_path,
        "renames": [],
        "skipped": [],
        "error": None,
    }

    # Load mesh
    mesh = unreal.EditorAssetLibrary.load_asset(mesh_path)
    if mesh is None:
        result["error"] = "Failed to load asset"
        return result

    if not isinstance(mesh, unreal.SkeletalMesh):
        result["error"] = f"Not a SkeletalMesh (type: {mesh.get_class().get_name()})"
        return result

    # Read slots using same API as validation (get_editor_property)
    try:
        materials = mesh.get_editor_property("materials")
    except Exception as e:
        result["error"] = f"Error reading materials: {e}"
        return result

    renamed_any = False

    for missing_slot in missing_slots:
        current_names = [
            str(mat.get_editor_property("material_slot_name"))
            for mat in materials
        ]
        match = find_best_match(missing_slot, current_names)

        if not match:
            result["skipped"].append({
                "target": missing_slot,
                "reason": "No matching slot found",
                "existing": current_names,
            })
            unreal.log_warning(
                f"[{LOG_TAG}] {mesh_path}: No match for '{missing_slot}' "
                f"in {current_names}"
            )
            continue

        # Rename the matching slot
        for i, mat_slot in enumerate(materials):
            name = str(mat_slot.get_editor_property("material_slot_name"))
            if name == match:
                mat_slot.set_editor_property(
                    "material_slot_name", unreal.Name(missing_slot)
                )
                materials[i] = mat_slot
                result["renames"].append({"from": match, "to": missing_slot})
                renamed_any = True
                unreal.log(
                    f"[{LOG_TAG}] {mesh_path}: '{match}' -> '{missing_slot}'"
                )
                break

    # Write modified materials back to mesh
    if renamed_any:
        try:
            mesh.modify()
            mesh.set_editor_property("materials", materials)
            unreal.log(f"[{LOG_TAG}] Modified: {mesh_path}")
        except Exception as e:
            result["error"] = f"Modify failed: {e}"
            unreal.log_error(f"[{LOG_TAG}] Modify failed for {mesh_path}: {e}")

    return result


# ---------------------------------------------------------------------------
# JSON output
# ---------------------------------------------------------------------------

def save_json(data, name):
    """Save result JSON to output directory."""
    output_dir = os.path.join(
        __import__("os").path.expanduser("~"), ".agent-local", "private", "unreal",
        "mat-slot-rename"
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

def main():
    # Load latest validation JSON
    validation_data, source_file = get_latest_validation_json()
    if not validation_data:
        return

    source_name = validation_data.get("name", "Unknown")

    # Get meshes that need renaming
    invalid_meshes = get_invalid_meshes(validation_data)
    if not invalid_meshes:
        unreal.log(f"[{LOG_TAG}] No invalid meshes found. Nothing to rename.")
        return

    unreal.log(
        f"[{LOG_TAG}] Found {len(invalid_meshes)} mesh(es) to process"
    )

    # Process each mesh
    results = []
    renamed_count = 0
    failed_count = 0

    for mesh_info in invalid_meshes:
        result = rename_slots_on_mesh(
            mesh_info["mesh_path"],
            mesh_info["missing_slots"],
            mesh_info["existing_slots"],
        )
        results.append(result)

        if result["renames"] and not result["error"]:
            renamed_count += 1
        elif result["error"] or result["skipped"]:
            failed_count += 1

    # Build output
    data = {
        "source": source_name,
        "source_file": source_file,
        "executed_at": datetime.now().isoformat(timespec="seconds"),
        "total_meshes": len(invalid_meshes),
        "renamed": renamed_count,
        "failed": failed_count,
        "results": results,
    }

    save_json(data, source_name)

    unreal.log(
        f"[{LOG_TAG}] Done. {renamed_count} renamed, "
        f"{failed_count} failed out of {len(invalid_meshes)} meshes."
    )


main()
