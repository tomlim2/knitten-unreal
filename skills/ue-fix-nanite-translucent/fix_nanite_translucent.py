"""
Find selected Translucent materials, trace their Static Mesh referencers,
and disable Nanite on any that have it enabled.

Run inside UE Editor Python console:
    exec(open(__import__("os").path.expanduser(r"~\\.agent-local\\skills\\ue-fix-nanite-translucent\\fix_nanite_translucent.py")).read())

Supports Material and MaterialInstanceConstant assets.
"""

import unreal


BLEND_MODE_NAMES = {
    0: "Opaque",
    1: "Masked",
    2: "Translucent",
    3: "Additive",
    4: "Modulate",
    5: "AlphaComposite",
    6: "AlphaHoldout",
}

TAG = "NaniteFix"


def get_blend_mode_name(material):
    """Get blend mode as string. Works for both Material and MaterialInstance."""
    try:
        val = material.get_editor_property("blend_mode")
        # UE enum: try .value, int(), repr fallback
        if isinstance(val, int):
            return BLEND_MODE_NAMES.get(val, str(val))
        if hasattr(val, 'value'):
            return BLEND_MODE_NAMES.get(val.value, str(val))
        # repr fallback: "BlendMode.TRANSLUCENT" -> extract name
        val_str = str(val)
        for k, v in BLEND_MODE_NAMES.items():
            if v.upper() in val_str.upper():
                return v
        return val_str
    except Exception:
        return "Unknown"


def is_translucent(material):
    """Check if material blend mode is Translucent."""
    try:
        val = material.get_editor_property("blend_mode")
        if isinstance(val, int):
            return val == 2
        if hasattr(val, 'value'):
            return val.value == 2
        # string fallback
        return "TRANSLUCENT" in str(val).upper() and "THIN" not in str(val).upper()
    except Exception:
        return False


def find_static_mesh_referencers(asset_path):
    """Find all Static Meshes that reference the given asset."""
    registry = unreal.AssetRegistryHelpers.get_asset_registry()

    # Get package name from full path (e.g. /Game/Foo/Bar.Bar -> /Game/Foo/Bar)
    package_name = asset_path.split('.')[0] if '.' in asset_path else asset_path

    dep_options = unreal.AssetRegistryDependencyOptions()
    dep_options.include_soft_package_references = True
    dep_options.include_hard_package_references = True
    dep_options.include_searchable_names = False
    dep_options.include_soft_management_references = False
    dep_options.include_hard_management_references = False

    referencers = registry.get_referencers(package_name, dep_options)

    meshes = []
    for ref_path in referencers:
        try:
            ref_str = str(ref_path)
            # Skip engine/script paths
            if ref_str.startswith('/Script/') or ref_str.startswith('/Engine/'):
                continue
            ref_asset = unreal.EditorAssetLibrary.load_asset(ref_str)
            if ref_asset is None:
                continue
            if isinstance(ref_asset, unreal.StaticMesh):
                meshes.append(ref_asset)
        except Exception:
            continue
    return meshes


def is_nanite_enabled(static_mesh):
    """Check if Nanite is enabled on a Static Mesh."""
    try:
        settings = static_mesh.get_editor_property("nanite_settings")
        return settings.get_editor_property("enabled")
    except Exception:
        return False


def disable_nanite(static_mesh):
    """Disable Nanite on a Static Mesh and save."""
    try:
        settings = static_mesh.get_editor_property("nanite_settings")
        settings.set_editor_property("enabled", False)
        static_mesh.set_editor_property("nanite_settings", settings)
        unreal.EditorAssetLibrary.save_loaded_asset(static_mesh)
        return True
    except Exception as e:
        unreal.log_error(f"[{TAG}] Failed to disable Nanite on '{static_mesh.get_name()}': {e}")
        return False


def main():
    utility = unreal.EditorUtilityLibrary
    selected = utility.get_selected_assets()

    if not selected:
        unreal.log_warning(f"[{TAG}] No assets selected. Select materials in Content Browser.")
        return

    translucent_mats = []
    skipped = 0

    for asset in selected:
        if isinstance(asset, (unreal.MaterialInstanceConstant, unreal.Material)):
            if is_translucent(asset):
                translucent_mats.append(asset)
                unreal.log(f"[{TAG}] Translucent: {asset.get_path_name()} (blend: {get_blend_mode_name(asset)})")
            else:
                skipped += 1
                unreal.log(f"[{TAG}] Skipping non-translucent: {asset.get_name()} (blend: {get_blend_mode_name(asset)})")
        else:
            skipped += 1
            unreal.log(f"[{TAG}] Skipping non-material: {asset.get_name()} ({asset.get_class().get_name()})")

    if not translucent_mats:
        unreal.log_warning(f"[{TAG}] No Translucent materials found in selection.")
        return

    unreal.log(f"[{TAG}] Found {len(translucent_mats)} Translucent material(s), scanning referencers...")

    total_meshes_found = 0
    total_nanite_disabled = 0

    for mat in translucent_mats:
        mat_path = mat.get_path_name()
        meshes = find_static_mesh_referencers(mat_path)

        if not meshes:
            unreal.log(f"[{TAG}]   {mat.get_name()}: no Static Mesh referencers")
            continue

        for mesh in meshes:
            total_meshes_found += 1
            if is_nanite_enabled(mesh):
                mesh_name = mesh.get_path_name()
                if disable_nanite(mesh):
                    total_nanite_disabled += 1
                    unreal.log_warning(f"[{TAG}]   DISABLED Nanite: {mesh_name} (ref by {mat.get_name()})")
                else:
                    unreal.log_error(f"[{TAG}]   FAILED to disable Nanite: {mesh_name}")
            else:
                unreal.log(f"[{TAG}]   OK (Nanite off): {mesh.get_name()} (ref by {mat.get_name()})")

    unreal.log(f"[{TAG}] === Summary ===")
    unreal.log(f"[{TAG}] Translucent materials: {len(translucent_mats)}")
    unreal.log(f"[{TAG}] Static Mesh referencers: {total_meshes_found}")
    unreal.log(f"[{TAG}] Nanite disabled: {total_nanite_disabled}")


main()
