"""
Apply suggested renames from a validation batch JSON.

Run inside UE Editor Python console:
    exec(open(__import__("os").path.expanduser(r"~\\.agent-local\\skills\\ue-validate-asset-name\\rename_assets.py")).read())

Reads the LATEST batch JSON from .agent-local/private/unreal/name-validate/
and renames assets that have suggested_name != null.

Set RENAME_FILTER before execution to limit which assets get renamed.
"""

import unreal
import json
import os
import glob


# ---------------------------------------------------------------------------
# Configuration — set before running
# ---------------------------------------------------------------------------

# Optional: only rename assets whose name is in this list.
# If empty, renames ALL assets with suggested names.
RENAME_FILTER = []  # e.g., ["BadName1", "BadName2"]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    batch_dir = os.path.join(
        __import__("os").path.expanduser("~"), ".agent-local", "private", "unreal", "name-validate"
    )

    # Find latest batch file
    pattern = os.path.join(batch_dir, "batch_*.json")
    files = sorted(glob.glob(pattern), reverse=True)

    if not files:
        unreal.log_error("[NameRename] No batch files found in name-validate directory.")
        return

    latest = files[0]
    unreal.log(f"[NameRename] Reading: {latest}")

    with open(latest, "r", encoding="utf-8") as f:
        batch = json.load(f)

    subsystem = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)

    renamed = 0
    skipped = 0
    failed = 0

    for entry in batch.get("assets", []):
        suggested = entry.get("suggested_name")
        if not suggested:
            continue

        old_name = entry["name"]
        old_path = entry["path"]

        # Strip object path suffix (e.g. "/Game/X/Y.Y" -> "/Game/X/Y")
        package_path = old_path.split('.')[0] if '.' in old_path else old_path

        # Apply filter
        if RENAME_FILTER and old_name not in RENAME_FILTER:
            skipped += 1
            continue

        directory = package_path.rsplit('/', 1)[0]
        new_path = f"{directory}/{suggested}"

        # Check destination doesn't already exist
        if unreal.EditorAssetLibrary.does_asset_exist(new_path):
            unreal.log_error(f"[NameRename] SKIP: '{suggested}' already exists at {new_path}")
            skipped += 1
            continue

        # Load asset
        asset = unreal.EditorAssetLibrary.load_asset(package_path)
        if not asset:
            unreal.log_error(f"[NameRename] Could not load: {package_path}")
            failed += 1
            continue

        try:
            # rename_asset/rename_loaded_asset fail on CJK source paths.
            # Safe rename: duplicate to new path, then consolidate references.
            # consolidate_assets redirects ALL refs from old -> new asset.
            new_asset = subsystem.duplicate_loaded_asset(asset, new_path)
            if not new_asset:
                unreal.log_error(f"[NameRename] FAIL duplicate: '{old_name}' -> '{suggested}'")
                failed += 1
                continue

            # consolidate_assets returns int (number of objects consolidated).
            # 0 means no refs to redirect — still a valid rename.
            # Only exceptions indicate true failure.
            consolidated = subsystem.consolidate_assets(new_asset, [asset])
            unreal.EditorAssetLibrary.save_asset(new_path)
            unreal.log(f"[NameRename] OK: '{old_name}' -> '{suggested}' ({consolidated} ref(s) redirected)")
            renamed += 1
        except Exception as e:
            # Clean up the duplicate if it was created
            if unreal.EditorAssetLibrary.does_asset_exist(new_path):
                subsystem.delete_loaded_asset(
                    unreal.EditorAssetLibrary.load_asset(new_path)
                )
            unreal.log_error(f"[NameRename] Error renaming '{old_name}': {e}")
            failed += 1

    unreal.log(
        f"[NameRename] Done. {renamed} renamed, {skipped} skipped, {failed} failed"
    )


main()
