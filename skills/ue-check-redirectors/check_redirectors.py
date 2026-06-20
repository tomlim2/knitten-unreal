"""
Check for ObjectRedirectors in the UE project Content folder.

Run inside UE Editor Python console:
    exec(open(__import__("os").path.expanduser(r"~\\.agent-local\\skills\\ue-check-redirectors\\check_redirectors.py")).read())

Scans /Game/ for all ObjectRedirector assets, checks if destinations exist,
groups by folder, and saves results as JSON.

Output: .agent-local/private/unreal/check-redirectors/redirectors.json
"""

import unreal
import json
import os
from datetime import datetime
from collections import defaultdict


LOG_TAG = "CheckRedirectors"
SCAN_PATH = "/Game/"


# ---------------------------------------------------------------------------
# Redirector scanning
# ---------------------------------------------------------------------------

def find_all_redirectors(scan_path):
    """Find all ObjectRedirector assets under the given path using Asset Registry."""
    registry = unreal.AssetRegistryHelpers.get_asset_registry()

    ar_filter = unreal.ARFilter(
        class_names=["ObjectRedirector"],
        package_paths=[scan_path],
        recursive_paths=True,
    )

    assets = registry.get_assets(ar_filter)
    unreal.log(f"[{LOG_TAG}] Found {len(assets)} ObjectRedirector(s) under {scan_path}")
    return assets


def get_redirector_info(asset_data):
    """Extract redirector info from AssetData.

    A .uasset package can contain multiple sub-objects. When assets are renamed
    or moved, ObjectRedirectors are created as sub-objects pointing from old
    names to new ones. load_asset(package_name) follows the redirector
    transparently and returns the destination.

    - If load_asset returns an object: redirector is valid (destination exists)
    - If load_asset returns None: redirector is broken (destination missing)

    Returns dict with path, object_path, destination, broken.
    """
    package_name = str(asset_data.package_name)
    asset_name = str(asset_data.asset_name)

    # Full object path identifies this specific redirector within the package
    try:
        object_path = str(asset_data.object_path)
    except Exception:
        object_path = f"{package_name}.{asset_name}"

    # load_asset follows the redirector chain
    obj = unreal.EditorAssetLibrary.load_asset(package_name)

    if obj is None:
        return {
            "path": package_name,
            "object_path": object_path,
            "destination": None,
            "broken": True,
        }

    # Resolved successfully — extract destination info
    dest_full = obj.get_path_name()
    # Clean: /Game/Path/Asset.Asset -> /Game/Path/Asset
    if "." in dest_full:
        dest_path = dest_full.rsplit(".", 1)[0]
    else:
        dest_path = dest_full

    # Destination differs from source = asset was moved/renamed across packages
    # Destination same as source = sub-object redirector (renamed within package)
    moved = dest_path != package_name

    return {
        "path": package_name,
        "object_path": object_path,
        "destination": dest_path if moved else None,
        "broken": False,
    }


def get_folder_path(asset_path):
    """Extract folder path from full asset path.

    /Game/Character/Anime/OldName -> /Game/Character/Anime/
    """
    parts = asset_path.rsplit("/", 1)
    if len(parts) == 2:
        return parts[0] + "/"
    return "/"


# ---------------------------------------------------------------------------
# JSON output
# ---------------------------------------------------------------------------

def save_json(data):
    """Save result JSON to output directory."""
    output_dir = os.path.join(
        __import__("os").path.expanduser("~"), ".agent-local", "private", "unreal",
        "check-redirectors"
    )
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "redirectors.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    unreal.log(f"[{LOG_TAG}] Saved: {output_path}")
    return output_path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    unreal.log(f"[{LOG_TAG}] Scanning {SCAN_PATH} for ObjectRedirectors...")

    # Find all redirectors
    asset_data_list = find_all_redirectors(SCAN_PATH)

    if not asset_data_list:
        unreal.log(f"[{LOG_TAG}] No redirectors found. Project is clean.")
        data = {
            "scanned_path": SCAN_PATH,
            "scanned_at": datetime.now().isoformat(timespec="seconds"),
            "total_redirectors": 0,
            "broken_redirectors": 0,
            "by_folder": {},
            "redirectors": [],
        }
        save_json(data)
        return

    # Deduplicate by object_path (registry can return duplicates)
    seen = set()
    redirectors = []
    broken_count = 0
    folder_counts = defaultdict(int)

    for i, asset_data in enumerate(asset_data_list):
        package_name = str(asset_data.package_name)
        asset_name = str(asset_data.asset_name)
        object_key = f"{package_name}.{asset_name}"

        if object_key in seen:
            continue
        seen.add(object_key)

        unreal.log(f"[{LOG_TAG}] [{i + 1}/{len(asset_data_list)}] {object_key}")

        info = get_redirector_info(asset_data)

        if info["broken"]:
            broken_count += 1

        folder = get_folder_path(package_name)
        folder_counts[folder] += 1

        redirectors.append(info)

    # Sort by_folder by count descending
    by_folder = dict(
        sorted(folder_counts.items(), key=lambda x: x[1], reverse=True)
    )

    data = {
        "scanned_path": SCAN_PATH,
        "scanned_at": datetime.now().isoformat(timespec="seconds"),
        "total_redirectors": len(redirectors),
        "broken_redirectors": broken_count,
        "by_folder": by_folder,
        "redirectors": redirectors,
    }

    save_json(data)
    unreal.log(
        f"[{LOG_TAG}] Done. {len(redirectors)} redirector(s) found "
        f"(from {len(asset_data_list)} registry entries, {len(asset_data_list) - len(redirectors)} duplicates removed), "
        f"{broken_count} broken."
    )


main()
