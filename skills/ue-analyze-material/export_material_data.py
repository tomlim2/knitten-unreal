"""
Export selected material data to JSON for Claude Code analysis.

Run inside UE Editor Python console:
    exec(open(__import__("os").path.expanduser(r"~\\.agent-local\\skills\\ue-analyze-material\\export_material_data.py")).read())

Supports Material, MaterialInstanceConstant, and MaterialFunction assets.
Output: .agent-local/private/unreal/material-analyze/{name}.json
"""

import unreal
import json
import os
from datetime import datetime


# ---------------------------------------------------------------------------
# Enum helpers
# ---------------------------------------------------------------------------

SHADING_MODEL_NAMES = {
    0: "Unlit",
    1: "Default Lit",
    2: "Subsurface",
    3: "Preintegrated Skin",
    4: "Clear Coat",
    5: "Subsurface Profile",
    6: "Two Sided Foliage",
    7: "Hair",
    8: "Cloth",
    9: "Eye",
    10: "SingleLayerWater",
    11: "Thin Translucent",
    12: "Strata",
}

BLEND_MODE_NAMES = {
    0: "Opaque",
    1: "Masked",
    2: "Translucent",
    3: "Additive",
    4: "Modulate",
    5: "AlphaComposite",
    6: "AlphaHoldout",
}

FUNCTION_INPUT_TYPE_NAMES = {
    0: "Scalar",
    1: "Vector2",
    2: "Vector3",
    3: "Vector4",
    4: "Texture2D",
    5: "TextureCube",
    6: "Texture2DArray",
    7: "VolumeTexture",
    8: "StaticBool",
    9: "MaterialAttributes",
    10: "TextureExternal",
}


def get_enum_name(value, names_map, fallback_prefix="Unknown"):
    """Resolve an enum int or object to a human-readable name."""
    if isinstance(value, int):
        return names_map.get(value, f"{fallback_prefix}({value})")
    # unreal enums expose .value or can be cast to int
    try:
        int_val = int(value)
        return names_map.get(int_val, f"{fallback_prefix}({int_val})")
    except (TypeError, ValueError):
        pass
    # UE Python enums repr as "<EnumType.NAME: N>" - extract the int
    import re
    match = re.search(r":\s*(\d+)\s*>", str(value))
    if match:
        int_val = int(match.group(1))
        return names_map.get(int_val, f"{fallback_prefix}({int_val})")
    return str(value)


# ---------------------------------------------------------------------------
# Material (base) extraction
# ---------------------------------------------------------------------------

def extract_base_material(material):
    """Extract data from a base Material asset."""
    data = _make_base_dict(material, "Material")

    # --- Properties ---
    try:
        data["properties"]["shading_model"] = get_enum_name(
            material.get_editor_property("shading_model"), SHADING_MODEL_NAMES, "ShadingModel"
        )
    except Exception:
        data["properties"]["shading_model"] = "Unknown"

    try:
        data["properties"]["blend_mode"] = get_enum_name(
            material.get_editor_property("blend_mode"), BLEND_MODE_NAMES, "BlendMode"
        )
    except Exception:
        data["properties"]["blend_mode"] = "Unknown"

    try:
        data["properties"]["two_sided"] = bool(material.get_editor_property("two_sided"))
    except Exception:
        data["properties"]["two_sided"] = None

    try:
        data["properties"]["opacity_mask_clip_value"] = float(
            material.get_editor_property("opacity_mask_clip_value")
        )
    except Exception:
        pass

    # --- Expressions (nodes) ---
    expressions = []
    try:
        expr_list = material.get_editor_property("expressions")
        for idx, expr in enumerate(expr_list):
            entry = {
                "index": idx,
                "class": expr.get_class().get_name(),
                "name": None,
                "position": {"x": 0, "y": 0},
            }
            # Parameter name
            try:
                entry["name"] = str(expr.get_editor_property("parameter_name"))
            except Exception:
                pass
            # Description (some nodes use desc)
            try:
                desc = str(expr.get_editor_property("desc"))
                if desc:
                    entry["name"] = entry["name"] or desc
            except Exception:
                pass
            # Node position
            try:
                entry["position"]["x"] = int(expr.get_editor_property("material_expression_editor_x"))
                entry["position"]["y"] = int(expr.get_editor_property("material_expression_editor_y"))
            except Exception:
                pass
            expressions.append(entry)
    except Exception as e:
        unreal.log_warning(f"[MaterialAnalyze] Could not read expressions: {e}")
    data["expressions"] = expressions

    # --- Connections ---
    connections = _extract_connections(material, expressions)
    data["connections"] = connections

    # --- Used textures ---
    textures = _extract_used_textures(material)
    data["textures"] = textures

    return data


def _extract_connections(material, expressions):
    """Try to extract connection info via MaterialEditingLibrary."""
    connections = []
    try:
        mel = unreal.MaterialEditingLibrary
    except AttributeError:
        unreal.log_warning("[MaterialAnalyze] MaterialEditingLibrary not available, skipping connections.")
        return connections

    # Material input pin names to check
    material_inputs = [
        "BaseColor", "Metallic", "Specular", "Roughness", "Anisotropy",
        "EmissiveColor", "Opacity", "OpacityMask", "Normal", "Tangent",
        "WorldPositionOffset", "SubsurfaceColor", "AmbientOcclusion",
        "Refraction", "PixelDepthOffset", "ShadingModel",
    ]

    # Build expression index lookup
    expr_list = []
    try:
        expr_list = list(material.get_editor_property("expressions"))
    except Exception:
        pass

    expr_to_idx = {}
    for idx, expr in enumerate(expr_list):
        expr_to_idx[expr] = idx

    # Check each material input
    for input_name in material_inputs:
        try:
            # get_material_property_input_node returns the expression connected to that input
            connected_expr = mel.get_material_property_input_node(material, input_name)
            if connected_expr is not None:
                from_idx = expr_to_idx.get(connected_expr)
                connections.append({
                    "from_node": from_idx if from_idx is not None else str(connected_expr.get_class().get_name()),
                    "from_output": "",
                    "to_node": "Material",
                    "to_input": input_name,
                })
        except Exception:
            pass

    return connections


def _extract_used_textures(material):
    """Get list of textures used by a material."""
    textures = []
    try:
        mel = unreal.MaterialEditingLibrary
        tex_list = mel.get_used_textures(material)
        for tex in tex_list:
            textures.append(tex.get_path_name())
    except Exception:
        # Fallback: scan expressions for texture references
        try:
            for expr in material.get_editor_property("expressions"):
                class_name = expr.get_class().get_name()
                if "Texture" in class_name:
                    try:
                        tex = expr.get_editor_property("texture")
                        if tex:
                            textures.append(tex.get_path_name())
                    except Exception:
                        pass
        except Exception:
            pass
    return textures


# ---------------------------------------------------------------------------
# MaterialInstance extraction
# ---------------------------------------------------------------------------

def extract_material_instance(mi):
    """Extract data from a MaterialInstanceConstant asset."""
    data = _make_base_dict(mi, "MaterialInstance")

    # --- Parent chain ---
    parent_chain = []
    current = mi
    while True:
        try:
            parent = current.get_editor_property("parent")
            if parent is None:
                break
            parent_chain.append(parent.get_path_name())
            current = parent
        except Exception:
            break
    data["parent_chain"] = parent_chain

    # --- Properties from the root parent ---
    if parent_chain:
        try:
            root = unreal.EditorAssetLibrary.load_asset(parent_chain[-1])
            if root and isinstance(root, unreal.Material):
                data["properties"]["shading_model"] = get_enum_name(
                    root.get_editor_property("shading_model"), SHADING_MODEL_NAMES, "ShadingModel"
                )
                data["properties"]["blend_mode"] = get_enum_name(
                    root.get_editor_property("blend_mode"), BLEND_MODE_NAMES, "BlendMode"
                )
                data["properties"]["two_sided"] = bool(root.get_editor_property("two_sided"))
        except Exception:
            pass

    # --- Scalar parameters ---
    try:
        scalar_params = mi.get_editor_property("scalar_parameter_values")
        for param in scalar_params:
            info = param.get_editor_property("parameter_info")
            data["parameters"]["scalar"].append({
                "name": str(info.get_editor_property("name")),
                "value": float(param.get_editor_property("parameter_value")),
            })
    except Exception as e:
        unreal.log_warning(f"[MaterialAnalyze] Could not read scalar params: {e}")

    # --- Vector parameters ---
    try:
        vector_params = mi.get_editor_property("vector_parameter_values")
        for param in vector_params:
            info = param.get_editor_property("parameter_info")
            val = param.get_editor_property("parameter_value")
            data["parameters"]["vector"].append({
                "name": str(info.get_editor_property("name")),
                "value": [float(val.r), float(val.g), float(val.b), float(val.a)],
            })
    except Exception as e:
        unreal.log_warning(f"[MaterialAnalyze] Could not read vector params: {e}")

    # --- Texture parameters ---
    try:
        texture_params = mi.get_editor_property("texture_parameter_values")
        for param in texture_params:
            info = param.get_editor_property("parameter_info")
            tex = param.get_editor_property("parameter_value")
            data["parameters"]["texture"].append({
                "name": str(info.get_editor_property("name")),
                "value": tex.get_path_name() if tex else None,
            })
    except Exception as e:
        unreal.log_warning(f"[MaterialAnalyze] Could not read texture params: {e}")

    # --- Static switch parameters ---
    try:
        static_params = mi.get_editor_property("static_parameters")
        if static_params:
            switch_params = static_params.get_editor_property("static_switch_parameters")
            for param in switch_params:
                data["parameters"].setdefault("static_switch", []).append({
                    "name": str(param.get_editor_property("parameter_info").get_editor_property("name")),
                    "value": bool(param.get_editor_property("value")),
                    "override": bool(param.get_editor_property("b_override")),
                })
    except Exception:
        pass  # Static params not always accessible

    return data


# ---------------------------------------------------------------------------
# MaterialFunction extraction
# ---------------------------------------------------------------------------

def extract_material_function(mf):
    """Extract data from a MaterialFunction asset."""
    data = _make_base_dict(mf, "MaterialFunction")

    # --- Properties ---
    try:
        data["properties"]["description"] = str(mf.get_editor_property("description"))
    except Exception:
        pass
    try:
        data["properties"]["expose_to_library"] = bool(mf.get_editor_property("expose_to_library"))
    except Exception:
        pass
    try:
        cats = mf.get_editor_property("library_categories_text")
        data["properties"]["library_categories"] = [str(c) for c in cats] if cats else []
    except Exception:
        pass

    # --- Expressions via ObjectIterator ---
    # MaterialFunction doesn't expose its expression list as a Python property,
    # so we find expressions whose outer object is this function.
    mf_path = mf.get_path_name()
    expr_objects = []
    for obj in unreal.ObjectIterator(unreal.MaterialExpression):
        outer = obj.get_outer()
        if outer and outer.get_path_name() == mf_path:
            expr_objects.append(obj)

    expressions = []
    function_inputs = []
    function_outputs = []
    textures = []

    for idx, expr in enumerate(expr_objects):
        class_name = expr.get_class().get_name()
        entry = {
            "index": idx,
            "class": class_name,
            "name": None,
            "position": {"x": 0, "y": 0},
        }
        # Try various name properties
        for prop in ("input_name", "output_name", "parameter_name", "desc"):
            try:
                val = str(expr.get_editor_property(prop))
                if val:
                    entry["name"] = val
                    break
            except Exception:
                pass
        # Node position
        try:
            entry["position"]["x"] = int(expr.get_editor_property("material_expression_editor_x"))
            entry["position"]["y"] = int(expr.get_editor_property("material_expression_editor_y"))
        except Exception:
            pass

        expressions.append(entry)

        # Collect function input info
        if "FunctionInput" in class_name:
            fi = {"index": idx, "name": entry["name"]}
            try:
                fi["input_type"] = get_enum_name(
                    expr.get_editor_property("input_type"),
                    FUNCTION_INPUT_TYPE_NAMES, "FunctionInput"
                )
            except Exception:
                pass
            try:
                fi["sort_priority"] = int(expr.get_editor_property("sort_priority"))
            except Exception:
                pass
            try:
                desc = str(expr.get_editor_property("description"))
                if desc:
                    fi["description"] = desc
            except Exception:
                pass
            function_inputs.append(fi)

        # Collect function output info
        elif "FunctionOutput" in class_name:
            fo = {"index": idx, "name": entry["name"]}
            try:
                fo["sort_priority"] = int(expr.get_editor_property("sort_priority"))
            except Exception:
                pass
            try:
                desc = str(expr.get_editor_property("description"))
                if desc:
                    fo["description"] = desc
            except Exception:
                pass
            function_outputs.append(fo)

        # Collect textures
        if "Texture" in class_name:
            try:
                tex = expr.get_editor_property("texture")
                if tex:
                    textures.append(tex.get_path_name())
            except Exception:
                pass

    data["expressions"] = expressions
    data["function_inputs"] = sorted(function_inputs, key=lambda x: x.get("sort_priority", 0))
    data["function_outputs"] = sorted(function_outputs, key=lambda x: x.get("sort_priority", 0))
    data["textures"] = textures

    # Remove irrelevant fields for MaterialFunction
    del data["properties"]["shading_model"]
    del data["properties"]["blend_mode"]
    del data["properties"]["two_sided"]
    del data["connections"]
    del data["parent_chain"]

    return data


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _make_base_dict(asset, asset_type):
    """Create the shared base dictionary for any material type."""
    return {
        "name": asset.get_name(),
        "path": asset.get_path_name(),
        "type": asset_type,
        "exported_at": datetime.now().isoformat(timespec="seconds"),
        "properties": {
            "shading_model": "Unknown",
            "blend_mode": "Unknown",
            "two_sided": None,
        },
        "expressions": [],
        "connections": [],
        "textures": [],
        "parameters": {
            "scalar": [],
            "vector": [],
            "texture": [],
        },
        "parent_chain": [],
    }


def save_json(data, name):
    """Save extracted data to the output directory."""
    output_dir = os.path.join(
        __import__("os").path.expanduser("~"), ".agent-local", "private", "unreal", "material-analyze"
    )
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{name}.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    unreal.log(f"[MaterialAnalyze] Saved: {output_path}")
    return output_path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    selected = unreal.EditorUtilityLibrary.get_selected_assets()

    if not selected:
        unreal.log_error("[MaterialAnalyze] No assets selected. Select a material in the Content Browser.")
        return

    processed = 0
    for asset in selected:
        if isinstance(asset, unreal.MaterialInstanceConstant):
            data = extract_material_instance(asset)
            save_json(data, data["name"])
            unreal.log(
                f"[MaterialAnalyze] MaterialInstance '{data['name']}' - "
                f"{len(data['parameters']['scalar'])} scalar, "
                f"{len(data['parameters']['vector'])} vector, "
                f"{len(data['parameters']['texture'])} texture params, "
                f"parent chain depth: {len(data['parent_chain'])}"
            )
            processed += 1

        elif isinstance(asset, unreal.MaterialFunction):
            data = extract_material_function(asset)
            save_json(data, data["name"])
            unreal.log(
                f"[MaterialAnalyze] MaterialFunction '{data['name']}' - "
                f"{len(data['expressions'])} expressions, "
                f"{len(data['function_inputs'])} inputs, "
                f"{len(data['function_outputs'])} outputs"
            )
            processed += 1

        elif isinstance(asset, unreal.Material):
            data = extract_base_material(asset)
            save_json(data, data["name"])
            unreal.log(
                f"[MaterialAnalyze] Material '{data['name']}' - "
                f"{len(data['expressions'])} expressions, "
                f"{len(data['connections'])} connections, "
                f"{len(data['textures'])} textures"
            )
            processed += 1

        else:
            unreal.log_warning(
                f"[MaterialAnalyze] Skipping '{asset.get_name()}' - "
                f"not a Material, MaterialInstance, or MaterialFunction "
                f"(type: {asset.get_class().get_name()})"
            )

    if processed == 0:
        unreal.log_warning("[MaterialAnalyze] No materials found in selection.")
    else:
        unreal.log(f"[MaterialAnalyze] Done. Exported {processed} material(s).")


main()
