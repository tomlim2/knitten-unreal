import json
import math
import os

import unreal


DEFAULT_LEVEL = "/Game/Levels/Lvl_MCPPCG"
DEFAULT_BLOCKS = 4
DEFAULT_BLOCK_SIZE = 1800.0
DEFAULT_ROAD_WIDTH = 260.0
DEFAULT_TERRAIN_TILES = 28
DEFAULT_ROAD_SEGMENTS = 24
CUBE_SIZE_CM = 100.0
MATERIAL_DIR = "/Game/Knitten/Materials/BoxCity"


def env_int(name, default):
    value = os.environ.get(name)
    if value in (None, ""):
        return default
    return int(value)


def env_float(name, default):
    value = os.environ.get(name)
    if value in (None, ""):
        return default
    return float(value)


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


def destroy_actor(actor):
    actor_subsystem = get_actor_subsystem()
    if actor_subsystem is not None:
        actor_subsystem.destroy_actor(actor)
    else:
        unreal.EditorLevelLibrary.destroy_actor(actor)


def load_first_asset(paths):
    for path in paths:
        asset = unreal.EditorAssetLibrary.load_asset(path)
        if asset is not None:
            return asset, path
    return None, None


def cube_mesh():
    mesh, path = load_first_asset(
        [
            "/Engine/BasicShapes/Cube.Cube",
            "/Game/LevelPrototyping/Meshes/SM_Cube.SM_Cube",
            "/Game/LevelPrototyping/Meshes/SM_ChamferCube.SM_ChamferCube",
        ]
    )
    if mesh is None:
        raise RuntimeError("unable to load a cube static mesh")
    return mesh, path


def optional_material(paths):
    material, _path = load_first_asset(paths)
    return material


def save_asset(asset):
    try:
        return bool(unreal.EditorAssetLibrary.save_loaded_asset(asset))
    except Exception:
        return bool(unreal.EditorAssetLibrary.save_asset(asset.get_path_name()))


def create_solid_material(asset_name, color, roughness=0.88, specular=0.12):
    asset_path = "%s/%s" % (MATERIAL_DIR, asset_name)
    if unreal.EditorAssetLibrary.does_asset_exist(asset_path):
        existing = unreal.EditorAssetLibrary.load_asset(asset_path)
        if existing is not None:
            return existing, False

    unreal.EditorAssetLibrary.make_directory(MATERIAL_DIR)
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
    unreal.MaterialEditingLibrary.connect_material_property(base_color, "", unreal.MaterialProperty.MP_BASE_COLOR)

    roughness_node = unreal.MaterialEditingLibrary.create_material_expression(
        material,
        unreal.MaterialExpressionConstant,
        -420,
        120,
    )
    roughness_node.set_editor_property("r", roughness)
    unreal.MaterialEditingLibrary.connect_material_property(roughness_node, "", unreal.MaterialProperty.MP_ROUGHNESS)

    specular_node = unreal.MaterialEditingLibrary.create_material_expression(
        material,
        unreal.MaterialExpressionConstant,
        -420,
        240,
    )
    specular_node.set_editor_property("r", specular)
    unreal.MaterialEditingLibrary.connect_material_property(specular_node, "", unreal.MaterialProperty.MP_SPECULAR)

    unreal.MaterialEditingLibrary.layout_material_expressions(material)
    errors = unreal.MaterialEditingLibrary.recompile_material(material)
    if errors:
        raise RuntimeError("material compile failed for %s: %s" % (asset_path, errors))

    save_asset(material)
    return material, True


def spawn_static_mesh(label, mesh, location, scale, material=None):
    actor_subsystem = get_actor_subsystem()
    unreal_location = unreal.Vector(float(location[0]), float(location[1]), float(location[2]))
    unreal_rotation = unreal.Rotator(0.0, 0.0, 0.0)

    if actor_subsystem is not None:
        actor = actor_subsystem.spawn_actor_from_class(unreal.StaticMeshActor, unreal_location, unreal_rotation)
    else:
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, unreal_location, unreal_rotation)

    actor.set_actor_label(label)
    actor.set_actor_scale3d(unreal.Vector(float(scale[0]), float(scale[1]), float(scale[2])))
    component = actor.static_mesh_component
    component.set_static_mesh(mesh)
    if material is not None:
        component.set_material(0, material)
    return actor


def cm_to_cube_scale(x, y, z):
    return (x / CUBE_SIZE_CM, y / CUBE_SIZE_CM, z / CUBE_SIZE_CM)


def terrain_height(x, y):
    broad_ridge = math.sin((x * 0.72 + y * 0.18) / 1850.0 + 0.4) * 58.0
    cross_swell = math.cos((x * 0.24 - y * 0.86) / 2300.0 - 0.9) * 42.0
    small_roll = math.sin((x + y) / 980.0) * 16.0
    center_softener = 1.0 - 0.16 * math.exp(-((x / 2800.0) ** 2 + (y / 2800.0) ** 2))
    return (broad_ridge + cross_swell + small_roll) * center_softener


def footprint_height(x, y, half_width, half_depth):
    sample_x = min(max(half_width * 0.62, 80.0), 420.0)
    sample_y = min(max(half_depth * 0.62, 80.0), 420.0)
    samples = [
        terrain_height(x, y),
        terrain_height(x - sample_x, y - sample_y),
        terrain_height(x + sample_x, y - sample_y),
        terrain_height(x - sample_x, y + sample_y),
        terrain_height(x + sample_x, y + sample_y),
    ]
    return max(samples)


def is_generated_terrain(label):
    return (
        label == "Landscape_Base_Box"
        or label.startswith("Landscape_Terrain_")
        or label.startswith("Road_NS_")
        or label.startswith("Road_EW_")
    )


def is_building(label):
    return label.startswith("Building_") or label.startswith("District_Marker_")


def clear_generated_surface():
    deleted = 0
    for actor in get_all_actors():
        if actor is None:
            continue
        if is_generated_terrain(actor.get_actor_label()):
            destroy_actor(actor)
            deleted += 1
    return deleted


def make_terrain(mesh, material, city_width, tile_count, margin):
    terrain_size = city_width + margin * 2.0
    tile_size = terrain_size / float(tile_count)
    terrain_base_z = -220.0
    spawned = 0

    for row in range(tile_count):
        y = -terrain_size / 2.0 + tile_size * (row + 0.5)
        for col in range(tile_count):
            x = -terrain_size / 2.0 + tile_size * (col + 0.5)
            top_z = terrain_height(x, y)
            thickness = max(40.0, top_z - terrain_base_z)
            location_z = terrain_base_z + thickness / 2.0
            spawn_static_mesh(
                "Landscape_Terrain_R%02d_C%02d" % (row, col),
                mesh,
                (x, y, location_z),
                cm_to_cube_scale(tile_size + 8.0, tile_size + 8.0, thickness),
                material,
            )
            spawned += 1

    return spawned


def make_roads(mesh, material, blocks, block_size, road_width, city_width, road_segments):
    half = city_width / 2.0
    segment_len = city_width / float(road_segments)
    road_thickness = 10.0
    spawned = 0

    for index in range(blocks + 1):
        offset = -half + road_width / 2.0 + index * (block_size + road_width)

        for segment in range(road_segments):
            y = -half + segment_len * (segment + 0.5)
            z = terrain_height(offset, y) + road_thickness / 2.0 + 3.0
            spawn_static_mesh(
                "Road_NS_%02d_S%02d" % (index, segment),
                mesh,
                (offset, y, z),
                cm_to_cube_scale(road_width, segment_len + 12.0, road_thickness),
                material,
            )
            spawned += 1

            x = -half + segment_len * (segment + 0.5)
            z = terrain_height(x, offset) + road_thickness / 2.0 + 5.0
            spawn_static_mesh(
                "Road_EW_%02d_S%02d" % (index, segment),
                mesh,
                (x, offset, z),
                cm_to_cube_scale(segment_len + 12.0, road_width, road_thickness),
                material,
            )
            spawned += 1

    return spawned


def conform_buildings():
    moved = 0
    samples = []
    for actor in get_all_actors():
        if actor is None:
            continue
        label = actor.get_actor_label()
        if not is_building(label):
            continue

        location = actor.get_actor_location()
        scale = actor.get_actor_scale3d()
        width = abs(float(scale.x)) * CUBE_SIZE_CM
        depth = abs(float(scale.y)) * CUBE_SIZE_CM
        height = abs(float(scale.z)) * CUBE_SIZE_CM
        base_z = footprint_height(float(location.x), float(location.y), width / 2.0, depth / 2.0) + 2.0
        new_z = base_z + height / 2.0
        actor.set_actor_location(unreal.Vector(float(location.x), float(location.y), float(new_z)), False, True)
        moved += 1

        if len(samples) < 10:
            samples.append(
                {
                    "actor": label,
                    "x": round(float(location.x), 2),
                    "y": round(float(location.y), 2),
                    "base_z": round(base_z, 2),
                    "height": round(height, 2),
                    "new_z": round(new_z, 2),
                }
            )

    return moved, samples


def main():
    level_path = os.environ.get("KNITTEN_UNREAL_LEVEL", DEFAULT_LEVEL)
    blocks = env_int("KNITTEN_UNREAL_CITY_BLOCKS", DEFAULT_BLOCKS)
    block_size = env_float("KNITTEN_UNREAL_BLOCK_SIZE", DEFAULT_BLOCK_SIZE)
    road_width = env_float("KNITTEN_UNREAL_ROAD_WIDTH", DEFAULT_ROAD_WIDTH)
    terrain_tiles = env_int("KNITTEN_UNREAL_TERRAIN_TILES", DEFAULT_TERRAIN_TILES)
    road_segments = env_int("KNITTEN_UNREAL_ROAD_SEGMENTS", DEFAULT_ROAD_SEGMENTS)
    margin = env_float("KNITTEN_UNREAL_TERRAIN_MARGIN", 800.0)

    if terrain_tiles < 4:
        raise RuntimeError("KNITTEN_UNREAL_TERRAIN_TILES must be >= 4")
    if road_segments < 4:
        raise RuntimeError("KNITTEN_UNREAL_ROAD_SEGMENTS must be >= 4")

    load_level(level_path)
    mesh, mesh_path = cube_mesh()

    terrain_material, terrain_material_created = create_solid_material(
        "M_BoxCity_Terrain_MutedGrass",
        (0.18, 0.34, 0.20),
        0.93,
        0.08,
    )
    road_material = optional_material(
        [
            "/Game/LevelPrototyping/Materials/MI_PrototypeGrid_TopDark.MI_PrototypeGrid_TopDark",
            "/Game/LevelPrototyping/Materials/MI_PrototypeGrid_Gray.MI_PrototypeGrid_Gray",
        ]
    )
    if road_material is None:
        road_material, _road_material_created = create_solid_material(
            "M_BoxCity_Road_Dark",
            (0.035, 0.04, 0.045),
            0.78,
            0.18,
        )

    city_width = blocks * block_size + (blocks + 1) * road_width
    deleted = clear_generated_surface()
    terrain_spawned = make_terrain(mesh, terrain_material, city_width, terrain_tiles, margin)
    roads_spawned = make_roads(mesh, road_material, blocks, block_size, road_width, city_width, road_segments)
    buildings_moved, building_samples = conform_buildings()

    saved_level = bool(get_level_subsystem().save_current_level())
    actor_count = len(get_all_actors())

    payload = {
        "level": level_path,
        "saved_level": saved_level,
        "actor_count": actor_count,
        "deleted_previous_surface_actor_count": deleted,
        "mesh": mesh_path,
        "city_width": city_width,
        "terrain_tiles": terrain_tiles,
        "terrain_actor_count": terrain_spawned,
        "terrain_material": terrain_material.get_path_name(),
        "terrain_material_created": terrain_material_created,
        "road_segments_per_axis": road_segments,
        "road_actor_count": roads_spawned,
        "buildings_moved": buildings_moved,
        "sample_building_positions": building_samples,
        "height_range_sample_cm": {
            "min": round(min(terrain_height(x, y) for x in (-city_width / 2.0, 0.0, city_width / 2.0) for y in (-city_width / 2.0, 0.0, city_width / 2.0)), 2),
            "max": round(max(terrain_height(x, y) for x in (-city_width / 2.0, 0.0, city_width / 2.0) for y in (-city_width / 2.0, 0.0, city_width / 2.0)), 2),
        },
    }

    print("KNITTEN_UNREAL_TERRAIN_CONFORM_BEGIN")
    print(json.dumps(payload, indent=2, sort_keys=True))
    print("KNITTEN_UNREAL_TERRAIN_CONFORM_END")


if __name__ == "__main__":
    main()
