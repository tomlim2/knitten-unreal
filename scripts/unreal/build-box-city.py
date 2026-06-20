import json
import os
import random

import unreal


DEFAULT_LEVEL = "/Game/Levels/Lvl_MCPPCG"
DEFAULT_BLOCKS = 4
DEFAULT_BLOCK_SIZE = 1800.0
DEFAULT_ROAD_WIDTH = 260.0
DEFAULT_SEED = 7
CUBE_SIZE_CM = 100.0


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


def ensure_level(level_path):
    level_subsystem = get_level_subsystem()
    if level_subsystem is None:
        raise RuntimeError("LevelEditorSubsystem is unavailable")

    if unreal.EditorAssetLibrary.does_asset_exist(level_path):
        if not level_subsystem.load_level(level_path):
            raise RuntimeError("failed to load level: %s" % level_path)
        return "loaded"

    if not level_subsystem.new_level(level_path, False):
        raise RuntimeError("failed to create level: %s" % level_path)
    return "created"


def get_all_actors():
    actor_subsystem = get_actor_subsystem()
    if actor_subsystem is not None:
        return list(actor_subsystem.get_all_level_actors())
    return list(unreal.EditorLevelLibrary.get_all_level_actors())


def clear_level():
    actors = get_all_actors()
    actor_subsystem = get_actor_subsystem()
    deleted = 0
    for actor in actors:
        if actor is None:
            continue
        if actor_subsystem is not None:
            actor_subsystem.destroy_actor(actor)
        else:
            unreal.EditorLevelLibrary.destroy_actor(actor)
        deleted += 1
    return deleted


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
    return load_first_asset(paths)


def spawn_static_mesh(label, mesh, location, scale, material=None):
    actor_subsystem = get_actor_subsystem()
    actor_class = unreal.StaticMeshActor
    unreal_location = unreal.Vector(float(location[0]), float(location[1]), float(location[2]))
    unreal_rotation = unreal.Rotator(0.0, 0.0, 0.0)

    if actor_subsystem is not None:
        actor = actor_subsystem.spawn_actor_from_class(actor_class, unreal_location, unreal_rotation)
    else:
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(actor_class, unreal_location, unreal_rotation)

    actor.set_actor_label(label)
    actor.set_actor_scale3d(unreal.Vector(float(scale[0]), float(scale[1]), float(scale[2])))
    component = actor.static_mesh_component
    component.set_static_mesh(mesh)
    if material is not None:
        component.set_material(0, material)
    return actor


def spawn_actor_from_class(actor_class_name, label, location, rotation=None):
    actor_class = getattr(unreal, actor_class_name, None)
    if actor_class is None:
        return None

    actor_subsystem = get_actor_subsystem()
    unreal_location = unreal.Vector(float(location[0]), float(location[1]), float(location[2]))
    unreal_rotation = rotation or unreal.Rotator(0.0, 0.0, 0.0)

    if actor_subsystem is not None:
        actor = actor_subsystem.spawn_actor_from_class(actor_class, unreal_location, unreal_rotation)
    else:
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(actor_class, unreal_location, unreal_rotation)
    actor.set_actor_label(label)
    return actor


def cm_to_cube_scale(x, y, z):
    return (x / CUBE_SIZE_CM, y / CUBE_SIZE_CM, z / CUBE_SIZE_CM)


def make_city(level_path, blocks, block_size, road_width, seed):
    rng = random.Random(seed)
    level_state = ensure_level(level_path)
    deleted = clear_level()
    mesh, mesh_path = cube_mesh()

    road_material, road_material_path = optional_material(
        [
            "/Game/LevelPrototyping/Materials/MI_PrototypeGrid_TopDark.MI_PrototypeGrid_TopDark",
            "/Game/LevelPrototyping/Materials/MI_PrototypeGrid_Gray.MI_PrototypeGrid_Gray",
        ]
    )
    building_material, building_material_path = optional_material(
        [
            "/Game/LevelPrototyping/Materials/MI_DefaultColorway.MI_DefaultColorway",
            "/Game/LevelPrototyping/Materials/MI_PrototypeGrid_Gray.MI_PrototypeGrid_Gray",
        ]
    )

    city_width = blocks * block_size + (blocks + 1) * road_width
    half = city_width / 2.0

    spawned = {
        "ground": 0,
        "roads": 0,
        "buildings": 0,
        "lights": 0,
        "cameras": 0,
    }

    spawn_static_mesh(
        "Landscape_Base_Box",
        mesh,
        (0.0, 0.0, -35.0),
        cm_to_cube_scale(city_width + 1200.0, city_width + 1200.0, 70.0),
    )
    spawned["ground"] += 1

    for index in range(blocks + 1):
        offset = -half + road_width / 2.0 + index * (block_size + road_width)
        spawn_static_mesh(
            "Road_NS_%02d" % index,
            mesh,
            (offset, 0.0, 4.0),
            cm_to_cube_scale(road_width, city_width, 8.0),
            road_material,
        )
        spawn_static_mesh(
            "Road_EW_%02d" % index,
            mesh,
            (0.0, offset, 6.0),
            cm_to_cube_scale(city_width, road_width, 10.0),
            road_material,
        )
        spawned["roads"] += 2

    lot_rows = 3
    lot_cols = 3
    lot_gap = 90.0
    usable = block_size - 2.0 * lot_gap
    lot_w = usable / lot_cols
    lot_d = usable / lot_rows

    for row in range(blocks):
        for col in range(blocks):
            block_min_x = -half + road_width + col * (block_size + road_width)
            block_min_y = -half + road_width + row * (block_size + road_width)
            for lot_y in range(lot_rows):
                for lot_x in range(lot_cols):
                    width = rng.uniform(lot_w * 0.48, lot_w * 0.78)
                    depth = rng.uniform(lot_d * 0.48, lot_d * 0.78)
                    base_height = rng.choice([240.0, 320.0, 420.0, 560.0, 760.0, 940.0])
                    height = base_height + rng.uniform(-40.0, 80.0)
                    x = block_min_x + lot_gap + lot_w * (lot_x + 0.5)
                    y = block_min_y + lot_gap + lot_d * (lot_y + 0.5)
                    z = height / 2.0

                    if row in (1, 2) and col in (1, 2) and lot_x == 1 and lot_y == 1:
                        height *= 1.75
                        width *= 1.05
                        depth *= 1.05

                    spawn_static_mesh(
                        "Building_B%02d_%02d_L%02d%02d" % (row, col, lot_y, lot_x),
                        mesh,
                        (x, y, z),
                        cm_to_cube_scale(width, depth, height),
                        building_material,
                    )
                    spawned["buildings"] += 1

    for index, (x_sign, y_sign) in enumerate([(-1, -1), (1, -1), (-1, 1), (1, 1)]):
        plaza_size = road_width * 0.75
        spawn_static_mesh(
            "District_Marker_%02d" % index,
            mesh,
            (x_sign * (half - road_width * 0.5), y_sign * (half - road_width * 0.5), plaza_size / 2.0),
            cm_to_cube_scale(plaza_size, plaza_size, plaza_size),
            building_material,
        )
        spawned["buildings"] += 1

    light = spawn_actor_from_class("DirectionalLight", "Sun_Key_Light", (0.0, 0.0, 900.0), unreal.Rotator(-45.0, -35.0, 0.0))
    if light is not None:
        try:
            light.get_component_by_class(unreal.DirectionalLightComponent).set_editor_property("intensity", 4.0)
        except Exception:
            pass
        spawned["lights"] += 1

    sky = spawn_actor_from_class("SkyLight", "Sky_Ambient_Light", (0.0, 0.0, 700.0))
    if sky is not None:
        spawned["lights"] += 1

    player_start = spawn_actor_from_class("PlayerStart", "PlayerStart_City_View", (-half * 0.8, -half * 0.8, 180.0), unreal.Rotator(0.0, 45.0, 0.0))
    if player_start is not None:
        spawned["cameras"] += 1

    camera = spawn_actor_from_class("CameraActor", "Camera_City_Overview", (-half * 0.75, -half * 0.95, 1500.0), unreal.Rotator(-32.0, 38.0, 0.0))
    if camera is not None:
        spawned["cameras"] += 1

    level_subsystem = get_level_subsystem()
    saved = bool(level_subsystem.save_current_level())
    actor_count = len(get_all_actors())

    return {
        "level": level_path,
        "level_state": level_state,
        "saved": saved,
        "deleted_actor_count": deleted,
        "actor_count": actor_count,
        "blocks": blocks,
        "block_size": block_size,
        "road_width": road_width,
        "city_width": city_width,
        "seed": seed,
        "cube_mesh": mesh_path,
        "road_material": road_material_path,
        "building_material": building_material_path,
        "spawned": spawned,
    }


def main():
    level_path = os.environ.get("KNITTEN_UNREAL_LEVEL", DEFAULT_LEVEL)
    blocks = env_int("KNITTEN_UNREAL_CITY_BLOCKS", DEFAULT_BLOCKS)
    block_size = env_float("KNITTEN_UNREAL_BLOCK_SIZE", DEFAULT_BLOCK_SIZE)
    road_width = env_float("KNITTEN_UNREAL_ROAD_WIDTH", DEFAULT_ROAD_WIDTH)
    seed = env_int("KNITTEN_UNREAL_SEED", DEFAULT_SEED)

    if blocks < 1:
        raise RuntimeError("KNITTEN_UNREAL_CITY_BLOCKS must be >= 1")
    if block_size <= 0.0:
        raise RuntimeError("KNITTEN_UNREAL_BLOCK_SIZE must be > 0")
    if road_width <= 0.0:
        raise RuntimeError("KNITTEN_UNREAL_ROAD_WIDTH must be > 0")
    if road_width >= block_size:
        raise RuntimeError("KNITTEN_UNREAL_ROAD_WIDTH must be smaller than block size")

    payload = make_city(level_path, blocks, block_size, road_width, seed)
    print("KNITTEN_UNREAL_CITY_BEGIN")
    print(json.dumps(payload, indent=2, sort_keys=True))
    print("KNITTEN_UNREAL_CITY_END")


if __name__ == "__main__":
    main()
