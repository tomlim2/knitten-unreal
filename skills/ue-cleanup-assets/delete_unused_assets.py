"""Delete unused assets listed in a scan JSON file.

This script runs inside UE Editor via remote execution.
Reads a scan JSON (from find_unused_assets.py) and deletes the unused assets.

Usage: Set SCAN_FILE_PATH before execution, or pass the latest scan file.
"""

import unreal
import json
import os
import glob


def find_latest_scan():
    """Find the most recent scan JSON file."""
    scan_dir = os.path.join(os.path.expanduser("~"), ".agent-local", "private", "unreal", "assets-cleanup")
    pattern = os.path.join(scan_dir, "scan_*.json")
    files = glob.glob(pattern)
    if not files:
        return None
    return max(files, key=os.path.getmtime)


def main():
    # Try environment variable first, then fall back to latest scan
    scan_file = os.environ.get("SCAN_FILE_PATH") or find_latest_scan()

    if not scan_file or not os.path.isfile(scan_file):
        unreal.log_error("No scan file found. Run find_unused_assets.py first.")
        return

    with open(scan_file, 'r') as f:
        scan_data = json.load(f)

    unused_assets = scan_data.get("unused_assets", [])
    if not unused_assets:
        print("No unused assets to delete.")
        return

    print(f"Deleting {len(unused_assets)} unused assets from scan: {os.path.basename(scan_file)}")

    deleted = []
    failed = []

    for entry in unused_assets:
        path = entry["path"]
        asset = unreal.EditorAssetLibrary.load_asset(path)

        if asset is None:
            print(f"  [SKIP] Asset not found: {path}")
            failed.append({"path": path, "reason": "not found"})
            continue

        if unreal.EditorAssetLibrary.delete_loaded_asset(asset):
            print(f"  [DELETED] {path}")
            deleted.append(path)
        else:
            print(f"  [FAILED] {path}")
            failed.append({"path": path, "reason": "delete failed"})

    print(f"\nResult: {len(deleted)} deleted, {len(failed)} failed")


main()
