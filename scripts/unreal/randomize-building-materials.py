import colorsys
import json
import os
import random

import unreal


DEFAULT_LEVEL = "/Game/Levels/Lvl_MCPPCG"
DEFAULT_SEED = 17
DEFAULT_COLOR_COUNT = 24
MATERIAL_DIR = "/Game/Knitten/Materials/BoxCity"


def env_int(name, default):
    value = os.environ.get(name)
    if value in (None, ""):
        return default
    return int(value)


def get_level_subsystem():
    return unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)


def get_actor_subsystem():
    cls = getattr(unreal, "EditorActorSubsystem", None)
    if cls is None:
        return None
    return unreal.get_editor_subsystem(cls)


def load_level(level_path):
    level_subsystem = get_level_subsystem()
    if level_subsystem is None:
        raise RuntimeError("LevelEditorSubsystem is unavailable")
    if not level_subsystem.load_level(level_path):
        raise RuntimeError("failed to load level: %s" % level_path)


def get_all_actors():
    actor_subsystem = get_actor_subsystem()
    if actor_subsystem is not None:
        return list(actor_subsystem.get_all_level_actors())
    return list(unreal.EditorLevelLibrary.get_all_level_actors())


def is_building_actor(actor):
    label = actor.get_actor_label()
    return label.startswith("Building_") or label.startswith("District_Marker_")


def building_actors():
    return [actor for actor in get_all_actors() if is_building_actor(actor)]


def save_asset(asset):
    try:
        return bool(unreal.EditorAssetLibrary.save_loaded_asset(asset))
    except Exception:
        return bool(unreal.EditorAssetLibrary.save_asset(asset.get_path_name()))


def create_material(asset_name, color):
    asset_path = "%s/%s" % (MATERIAL_DIR, asset_name)
    if unreal.EditorAssetLibrary.does_asset_exist(asset_path):
        existing = unreal.EditorAssetLibrary.load_asset(asset_path)
        if existing is not None:
            return existing, False

    tools = unreal.AssetToolsHelpers.get_asset_tools()
    material = tools.create_asset(asset_name, MATERIAL_DIR, unreal.Material, unreal.MaterialFactoryNew())
    if material is None:
        raise RuntimeError("failed to create material: %s" % asset_path)

    unreal.MaterialEditingLibrary.delete_all_material_expressions(material)

    base_color = unreal.MaterialEditingLibrary.create_material_expression(
        material,
        unreal.MaterialExpressionConstant3Vector,
        -420,
        -80,
    )
    base_color.set_editor_property("constant", unreal.LinearColor(color[0], color[1], color[2], 1.0))
    unreal.MaterialEditingLibrary.connect_material_property(
        base_color,
        "",
        unreal.MaterialProperty.MP_BASE_COLOR,
    )

    roughness = unreal.MaterialEditingLibrary.create_material_expression(
        material,
        unreal.MaterialExpressionConstant,
        -420,
        120,
    )
    roughness.set_editor_property("r", 0.82)
    unreal.MaterialEditingLibrary.connect_material_property(
        roughness,
        "",
        unreal.MaterialProperty.MP_ROUGHNESS,
    )

    specular = unreal.MaterialEditingLibrary.create_material_expression(
        material,
        unreal.MaterialExpressionConstant,
        -420,
        240,
    )
    specular.set_editor_property("r", 0.18)
    unreal.MaterialEditingLibrary.connect_material_property(
        specular,
        "",
        unreal.MaterialProperty.MP_SPECULAR,
    )

    unreal.MaterialEditingLibrary.layout_material_expressions(material)
    errors = unreal.MaterialEditingLibrary.recompile_material(material)
    if errors:
        raise RuntimeError("material compile failed for %s: %s" % (asset_path, errors))

    save_asset(material)
    return material, True


def make_palette(seed, count):
    if count < 1:
        raise RuntimeError("KNITTEN_UNREAL_COLOR_COUNT must be >= 1")

    rng = random.Random(seed)
    unreal.EditorAssetLibrary.make_directory(MATERIAL_DIR)
    materials = []
    created = 0
    colors = []

    for index in range(count):
        hue = (index / float(count) + rng.uniform(-0.018, 0.018)) % 1.0
        saturation = rng.uniform(0.45, 0.78)
        value = rng.uniform(0.48, 0.88)
        red, green, blue = colorsys.hsv_to_rgb(hue, saturation, value)
        color = (red, green, blue)
        material, was_created = create_material("M_BoxCity_Building_%02d" % index, color)
        if was_created:
            created += 1
        materials.append(material)
        colors.append(
            {
                "material": material.get_path_name(),
                "rgb": [round(red, 4), round(green, 4), round(blue, 4)],
            }
        )

    return materials, colors, created


def assign_material(actor, material):
    mesh_component = actor.static_mesh_component
    mesh_component.set_material(0, material)


def main():
    level_path = os.environ.get("KNITTEN_UNREAL_LEVEL", DEFAULT_LEVEL)
    seed = env_int("KNITTEN_UNREAL_SEED", DEFAULT_SEED)
    color_count = env_int("KNITTEN_UNREAL_COLOR_COUNT", DEFAULT_COLOR_COUNT)

    load_level(level_path)
    materials, colors, created_count = make_palette(seed, color_count)
    rng = random.Random(seed + 1009)
    actors = sorted(building_actors(), key=lambda actor: actor.get_actor_label())

    assignments = []
    for actor in actors:
        material = rng.choice(materials)
        assign_material(actor, material)
        assignments.append(
            {
                "actor": actor.get_actor_label(),
                "material": material.get_path_name(),
            }
        )

    saved_level = bool(get_level_subsystem().save_current_level())

    payload = {
        "level": level_path,
        "seed": seed,
        "color_count": color_count,
        "material_dir": MATERIAL_DIR,
        "materials_created": created_count,
        "materials_available": len(materials),
        "building_actor_count": len(actors),
        "saved_level": saved_level,
        "colors": colors,
        "sample_assignments": assignments[:12],
    }

    print("KNITTEN_UNREAL_RANDOM_MATERIALS_BEGIN")
    print(json.dumps(payload, indent=2, sort_keys=True))
    print("KNITTEN_UNREAL_RANDOM_MATERIALS_END")


if __name__ == "__main__":
    main()
