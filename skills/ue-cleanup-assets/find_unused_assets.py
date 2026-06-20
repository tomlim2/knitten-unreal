"""Scan selected UE assets for references and save results to JSON.

This script runs inside UE Editor via remote execution.
Select assets in Content Browser before running.

Output: .agent-local/private/unreal/assets-cleanup/scan_YYYYMMDD_HHMMSS.json
"""

import unreal
import json
import os
from datetime import datetime


def main():
    # Get selected assets
    selected_assets = unreal.EditorUtilityLibrary.get_selected_assets()
    if not selected_assets:
        unreal.log_error("No assets selected. Select assets in Content Browser first.")
        return

    asset_subsystem = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)

    unused_assets = []
    referenced_assets = []

    for asset in selected_assets:
        path_name = asset.get_path_name().split('.')[0]
        asset_name = asset.get_name()
        asset_type = asset.get_class().get_name()

        referencers = asset_subsystem.find_package_referencers_for_asset(path_name)
        referencer_count = len(referencers)

        entry = {
            "name": asset_name,
            "path": path_name,
            "type": asset_type
        }

        if referencer_count == 0:
            unused_assets.append(entry)
        else:
            entry["referencer_count"] = referencer_count
            referenced_assets.append(entry)

    # Build result
    result = {
        "scanned_at": datetime.now().isoformat(),
        "total_scanned": len(selected_assets),
        "unused_count": len(unused_assets),
        "unused_assets": unused_assets,
        "referenced_assets": referenced_assets
    }

    # Save to private directory
    output_dir = os.path.join(os.path.expanduser("~"), ".agent-local", "private", "unreal", "assets-cleanup")
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"scan_{timestamp}.json")

    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)

    # Print summary
    print(f"Scan complete: {len(selected_assets)} assets checked")
    print(f"  Unused: {len(unused_assets)}")
    print(f"  Referenced: {len(referenced_assets)}")
    print(f"  Saved to: {output_file}")

    for asset in unused_assets:
        print(f"  [UNUSED] {asset['path']}")

    for asset in referenced_assets:
        print(f"  [REFERENCED x{asset['referencer_count']}] {asset['path']}")


main()
