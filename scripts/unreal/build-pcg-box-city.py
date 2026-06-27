import json
import math
import os
import random
import time

import unreal


DEFAULT_LEVEL = "/Game/Levels/Lvl_MCPPCG"
PCG_DIR = "/Game/Knitten/PCG"
PCG_GRAPH_NAME = "PCG_BoxCity_Generator"
PCG_GRAPH_PATH = "%s/%s" % (PCG_DIR, PCG_GRAPH_NAME)
MATERIAL_DIR = "/Game/Knitten/Materials/BoxCity"
CUBE_SIZE_CM = 100.0


def env_int(name, default):
    value = os.environ.get(name)
    if value is None:
        return int(default)
    try:
        return int(value)
    except ValueError:
        raise RuntimeError("%s must be an integer, got %r" % (name, value))


def env_float(name, default):
    value = os.environ.get(name)
    if value is None:
        return float(default)
    try:
        return float(value)
    except ValueError:
        raise RuntimeError("%s must be a number, got %r" % (name, value))


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


def destroy_actor(actor):
    actor_subsystem = get_actor_subsystem()
    if actor_subsystem is not None:
        actor_subsystem.destroy_actor(actor)
    else:
        unreal.EditorLevelLibrary.destroy_actor(actor)


def spawn_actor(actor_class, label, location, rotation=None):
    actor_subsystem = get_actor_subsystem()
    unreal_location = unreal.Vector(float(location[0]), float(location[1]), float(location[2]))
    unreal_rotation = rotation or unreal.Rotator(0.0, 0.0, 0.0)

    if actor_subsystem is not None:
        actor = actor_subsystem.spawn_actor_from_class(actor_class, unreal_location, unreal_rotation)
    else:
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(actor_class, unreal_location, unreal_rotation)

    actor.set_actor_label(label)
    return actor


def spawn_static_mesh(label, mesh, location, scale, material=None):
    actor = spawn_actor(unreal.StaticMeshActor, label, location)
    actor.set_actor_scale3d(unreal.Vector(float(scale[0]), float(scale[1]), float(scale[2])))
    component = actor.static_mesh_component
    component.set_static_mesh(mesh)
    if material is not None:
        component.set_material(0, material)
    return actor


def clear_level():
    deleted = 0
    for actor in get_all_actors():
        if actor is None:
            continue
        destroy_actor(actor)
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


def cm_to_cube_scale(x, y, z):
    return (x / CUBE_SIZE_CM, y / CUBE_SIZE_CM, z / CUBE_SIZE_CM)


def terrain_height(x, y):
    broad_ridge = math.sin((x * 0.72 + y * 0.18) / 1850.0 + 0.4) * 58.0
    cross_swell = math.cos((x * 0.24 - y * 0.86) / 2300.0 - 0.9) * 42.0
    small_roll = math.sin((x + y) / 980.0) * 16.0
    center_softener = 1.0 - 0.16 * math.exp(-((x / 2800.0) ** 2 + (y / 2800.0) ** 2))
    return (broad_ridge + cross_swell + small_roll) * center_softener


def footprint_height(x, y, half_width, half_depth):
    sample_x = min(max(half_width * 0.82, 70.0), 460.0)
    sample_y = min(max(half_depth * 0.82, 70.0), 460.0)
    samples = [
        (x, y),
        (x - sample_x, y - sample_y),
        (x + sample_x, y - sample_y),
        (x - sample_x, y + sample_y),
        (x + sample_x, y + sample_y),
        (x - sample_x, y),
        (x + sample_x, y),
        (x, y - sample_y),
        (x, y + sample_y),
    ]
    return max(terrain_height(sample[0], sample[1]) for sample in samples)


def save_asset(asset):
    try:
        return bool(unreal.EditorAssetLibrary.save_loaded_asset(asset))
    except Exception:
        return bool(unreal.EditorAssetLibrary.save_asset(asset.get_path_name()))


def create_solid_material(asset_name, color, roughness=0.86, specular=0.12):
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


def building_material_palette(fallback):
    materials = []
    for index in range(24):
        path = "%s/M_BoxCity_Building_%02d.M_BoxCity_Building_%02d" % (MATERIAL_DIR, index, index)
        material = unreal.EditorAssetLibrary.load_asset(path)
        if material is not None:
            materials.append(material)
    return materials or [fallback]


def set_property(obj, name, value):
    obj.set_editor_property(name, value)


def attr_or_call(obj, name):
    value = getattr(obj, name)
    if callable(value):
        return value()
    return value


def pin_label(pin):
    properties = attr_or_call(pin, "properties")
    try:
        return properties.get_editor_property("label")
    except Exception:
        return properties.label


def input_label(node):
    pins = list(attr_or_call(node, "input_pins"))
    if not pins:
        return "In"
    return pin_label(pins[0])


def output_label(node):
    pins = list(attr_or_call(node, "output_pins"))
    if not pins:
        return "Out"
    return pin_label(pins[0])


def add_node(graph, settings_class, x, y):
    node, settings = graph.add_node_of_type(settings_class)
    try:
        node.set_node_position(unreal.Vector2D(float(x), float(y)))
    except Exception:
        pass
    return node, settings


def connect(graph, from_node, to_node):
    return graph.add_edge(from_node, output_label(from_node), to_node, input_label(to_node))


def weighted_selector_entry(mesh, material, weight=1):
    descriptor = unreal.PCGSoftISMComponentDescriptor()
    set_property(descriptor, "static_mesh", mesh)
    if material is not None:
        set_property(descriptor, "override_materials", [material])

    entry = unreal.PCGMeshSelectorWeightedEntry()
    set_property(entry, "descriptor", descriptor)
    set_property(entry, "weight", int(weight))
    return entry


def configure_spawner(settings, mesh, material):
    settings.set_mesh_selector_type(unreal.PCGMeshSelectorWeighted)
    set_property(settings, "apply_mesh_bounds_to_points", True)
    set_property(settings, "synchronous_load", True)

    selector = settings.get_editor_property("mesh_selector_parameters")
    set_property(selector, "mesh_entries", [weighted_selector_entry(mesh, material)])
    return selector


def add_mesh_branch(graph, name, mesh, material, grid_extents, cell_size, offset, scale_min, scale_max, node_y):
    grid_node, grid = add_node(graph, unreal.PCGCreatePointsGridSettings, -760, node_y)
    set_property(grid, "grid_extents", unreal.Vector(float(grid_extents[0]), float(grid_extents[1]), float(grid_extents[2])))
    set_property(grid, "cell_size", unreal.Vector(float(cell_size[0]), float(cell_size[1]), float(cell_size[2])))
    set_property(grid, "set_points_bounds", True)
    set_property(grid, "cull_points_outside_volume", False)
    set_property(grid, "point_steepness", 1.0)
    set_property(grid, "coordinate_space", unreal.PCGCoordinateSpace.WORLD)
    set_property(grid, "point_position", unreal.PCGPointPosition.CELL_CENTER)

    transform_node, transform = add_node(graph, unreal.PCGTransformPointsSettings, -360, node_y)
    set_property(transform, "offset_min", unreal.Vector(float(offset[0]), float(offset[1]), float(offset[2])))
    set_property(transform, "offset_max", unreal.Vector(float(offset[0]), float(offset[1]), float(offset[2])))
    set_property(transform, "absolute_offset", False)
    set_property(transform, "scale_min", unreal.Vector(float(scale_min[0]), float(scale_min[1]), float(scale_min[2])))
    set_property(transform, "scale_max", unreal.Vector(float(scale_max[0]), float(scale_max[1]), float(scale_max[2])))
    set_property(transform, "absolute_scale", True)
    set_property(transform, "uniform_scale", False)
    set_property(transform, "recompute_seed", True)

    spawner_node, spawner = add_node(graph, unreal.PCGStaticMeshSpawnerSettings, 60, node_y)
    configure_spawner(spawner, mesh, material)

    connect(graph, grid_node, transform_node)
    connect(graph, transform_node, spawner_node)
    return spawner_node


def create_pcg_graph(mesh, materials):
    if unreal.EditorAssetLibrary.does_asset_exist(PCG_GRAPH_PATH):
        unreal.EditorAssetLibrary.delete_asset(PCG_GRAPH_PATH)

    unreal.EditorAssetLibrary.make_directory(PCG_DIR)
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    graph = tools.create_asset(PCG_GRAPH_NAME, PCG_DIR, unreal.PCGGraph, unreal.PCGGraphFactory())
    if graph is None:
        raise RuntimeError("failed to create PCG graph: %s" % PCG_GRAPH_PATH)

    output = graph.get_output_node()
    try:
        output.set_node_position(unreal.Vector2D(560.0, 40.0))
    except Exception:
        pass

    branches = [
        add_mesh_branch(
            graph,
            "Terrain",
            mesh,
            materials["terrain"],
            (1.0, 1.0, 1.0),
            (20000.0, 20000.0, 20000.0),
            (0.0, 0.0, -10.0),
            (94.0, 94.0, 0.12),
            (94.0, 94.0, 0.12),
            -360,
        ),
        add_mesh_branch(
            graph,
            "Road NS",
            mesh,
            materials["road"],
            (4100.0, 1.0, 1.0),
            (2050.0, 20000.0, 20000.0),
            (0.0, 0.0, 4.0),
            (2.8, 88.0, 0.08),
            (2.8, 88.0, 0.08),
            -80,
        ),
        add_mesh_branch(
            graph,
            "Road EW",
            mesh,
            materials["road"],
            (1.0, 4100.0, 1.0),
            (20000.0, 2050.0, 20000.0),
            (0.0, 0.0, 6.0),
            (88.0, 2.8, 0.08),
            (88.0, 2.8, 0.08),
            200,
        ),
        add_mesh_branch(
            graph,
            "Buildings",
            mesh,
            materials["building"],
            (3650.0, 3650.0, 1.0),
            (520.0, 520.0, 20000.0),
            (0.0, 0.0, 620.0),
            (1.6, 1.6, 4.2),
            (3.6, 3.6, 11.5),
            500,
        ),
    ]

    for branch in branches:
        graph.add_edge(branch, output_label(branch), output, input_label(output))

    try:
        graph.force_notification_for_editor()
    except Exception:
        pass

    save_asset(graph)
    return graph


def get_pcg_component(actor):
    try:
        component = actor.get_editor_property("pcg_component")
        if component is not None:
            return component
    except Exception:
        pass
    return actor.get_component_by_class(unreal.PCGComponent)


def tick_editor(seconds=1.0):
    deadline = time.time() + float(seconds)
    while time.time() < deadline:
        try:
            unreal.EditorLevelLibrary.editor_invalidate_viewports()
        except Exception:
            pass
        time.sleep(0.05)


def instance_summary(actor):
    summary = {
        "pcg_components": 0,
        "instanced_static_mesh_components": 0,
        "instances": 0,
    }
    for component in actor.get_components_by_class(unreal.ActorComponent):
        if component is None:
            continue
        if isinstance(component, unreal.PCGComponent):
            summary["pcg_components"] += 1
        if isinstance(component, unreal.InstancedStaticMeshComponent):
            summary["instanced_static_mesh_components"] += 1
            try:
                summary["instances"] += int(component.get_instance_count())
            except Exception:
                pass
    return summary


def create_context_actors(graph, generate_pcg=False):
    pcg_volume = spawn_actor(unreal.PCGVolume, "PCG_BoxCity_Generator", (0.0, 0.0, 0.0))
    pcg_volume.set_actor_scale3d(unreal.Vector(48.0, 48.0, 6.0))

    pcg_component = get_pcg_component(pcg_volume)
    if pcg_component is None:
        raise RuntimeError("spawned PCGVolume has no PCGComponent")

    pcg_component.set_graph(graph)
    set_property(pcg_component, "seed", 84)
    set_property(pcg_component, "activated", bool(generate_pcg))
    set_property(pcg_component, "input_type", unreal.PCGComponentInput.ACTOR)
    set_property(pcg_component, "generation_trigger", unreal.PCGComponentGenerationTrigger.GENERATE_ON_DEMAND)
    set_property(pcg_component, "regenerate_in_editor", True)
    set_property(pcg_component, "ignore_landscape_tracking", True)

    if generate_pcg:
        pcg_component.cleanup_local(True)
        pcg_component.generate_local(True)
        tick_editor(1.0)

    light = spawn_actor(unreal.DirectionalLight, "Sun_Key_Light", (0.0, 0.0, 1200.0), unreal.Rotator(-48.0, -35.0, 0.0))
    try:
        light.get_component_by_class(unreal.DirectionalLightComponent).set_editor_property("intensity", 4.0)
    except Exception:
        pass

    spawn_actor(unreal.SkyLight, "Sky_Ambient_Light", (0.0, 0.0, 900.0))
    spawn_actor(unreal.PlayerStart, "PlayerStart_City_View", (-4400.0, -4400.0, 260.0), unreal.Rotator(0.0, 45.0, 0.0))

    return pcg_volume, pcg_component


def add_layout_item(layout, group, label, material_key, location, scale, material_index=None, meta=None):
    item = {
        "label": label,
        "material_key": material_key,
        "location": tuple(float(value) for value in location),
        "scale": tuple(float(value) for value in scale),
    }
    if material_index is not None:
        item["material_index"] = int(material_index)
    if meta:
        item["meta"] = meta
    layout[group].append(item)
    layout["summary"][group] += 1
    return item


def update_terrain_summary(summary, top_z):
    if summary["terrain_height_min"] is None:
        summary["terrain_height_min"] = top_z
        summary["terrain_height_max"] = top_z
        return
    summary["terrain_height_min"] = min(summary["terrain_height_min"], top_z)
    summary["terrain_height_max"] = max(summary["terrain_height_max"], top_z)


def generate_city_layout(
    blocks=4,
    block_size=1800.0,
    road_width=260.0,
    seed=84,
    terrain_tiles=32,
    road_segments=24,
):
    rng = random.Random(seed)
    city_width = blocks * block_size + (blocks + 1) * road_width
    half = city_width / 2.0

    layout = {
        "terrain": [],
        "roads": [],
        "buildings": [],
        "markers": [],
        "summary": {
            "generator": "terrain_aware_layout",
            "seed": seed,
            "blocks": blocks,
            "terrain": 0,
            "roads": 0,
            "buildings": 0,
            "markers": 0,
            "terrain_height_min": None,
            "terrain_height_max": None,
            "grounding_samples": [],
        },
    }

    terrain_size = city_width + 1400.0
    tile_size = terrain_size / float(terrain_tiles)
    terrain_base_z = -240.0
    for row in range(terrain_tiles):
        y = -terrain_size / 2.0 + tile_size * (row + 0.5)
        for col in range(terrain_tiles):
            x = -terrain_size / 2.0 + tile_size * (col + 0.5)
            top_z = terrain_height(x, y)
            thickness = max(48.0, top_z - terrain_base_z)
            center_z = terrain_base_z + thickness / 2.0
            add_layout_item(
                layout,
                "terrain",
                "PCGGenerated_Terrain_R%02d_C%02d" % (row, col),
                "terrain",
                (x, y, center_z),
                cm_to_cube_scale(tile_size + 4.0, tile_size + 4.0, thickness),
                meta={"top_z": round(top_z, 2), "base_z": terrain_base_z},
            )
            update_terrain_summary(layout["summary"], top_z)

    road_thickness = 12.0
    segment_len = city_width / float(road_segments)
    for index in range(blocks + 1):
        offset = -half + road_width / 2.0 + index * (block_size + road_width)
        for segment in range(road_segments):
            center = -half + segment_len * (segment + 0.5)
            ns_terrain_z = footprint_height(offset, center, road_width / 2.0, (segment_len + 18.0) / 2.0)
            ns_base_z = ns_terrain_z + 2.0
            add_layout_item(
                layout,
                "roads",
                "PCGGenerated_Road_NS_%02d_S%02d" % (index, segment),
                "road",
                (offset, center, ns_base_z + road_thickness / 2.0),
                cm_to_cube_scale(road_width, segment_len + 18.0, road_thickness),
                meta={"terrain_z": round(ns_terrain_z, 2), "base_z": round(ns_base_z, 2)},
            )
            ew_terrain_z = footprint_height(center, offset, (segment_len + 18.0) / 2.0, road_width / 2.0)
            ew_base_z = ew_terrain_z + 2.0
            add_layout_item(
                layout,
                "roads",
                "PCGGenerated_Road_EW_%02d_S%02d" % (index, segment),
                "road",
                (center, offset, ew_base_z + road_thickness / 2.0),
                cm_to_cube_scale(segment_len + 18.0, road_width, road_thickness),
                meta={"terrain_z": round(ew_terrain_z, 2), "base_z": round(ew_base_z, 2)},
            )

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
                    height = rng.choice([240.0, 320.0, 420.0, 560.0, 760.0, 940.0]) + rng.uniform(-30.0, 90.0)
                    x = block_min_x + lot_gap + lot_w * (lot_x + 0.5)
                    y = block_min_y + lot_gap + lot_d * (lot_y + 0.5)

                    if row in (1, 2) and col in (1, 2) and lot_x == 1 and lot_y == 1:
                        height *= 1.75
                        width *= 1.05
                        depth *= 1.05

                    material_index = row * blocks * lot_rows * lot_cols + col * lot_rows * lot_cols + lot_y * lot_cols + lot_x
                    terrain_z = footprint_height(x, y, width / 2.0, depth / 2.0)
                    base_z = terrain_z + 2.0
                    add_layout_item(
                        layout,
                        "buildings",
                        "PCGGenerated_Building_B%02d_%02d_L%02d%02d" % (row, col, lot_y, lot_x),
                        "building",
                        (x, y, base_z + height / 2.0),
                        cm_to_cube_scale(width, depth, height),
                        material_index=material_index,
                        meta={
                            "terrain_z": round(terrain_z, 2),
                            "base_z": round(base_z, 2),
                            "height": round(height, 2),
                        },
                    )
                    if len(layout["summary"]["grounding_samples"]) < 10:
                        layout["summary"]["grounding_samples"].append(
                            {
                                "label": "B%02d_%02d_L%02d%02d" % (row, col, lot_y, lot_x),
                                "terrain_z": round(terrain_z, 2),
                                "base_z": round(base_z, 2),
                                "height": round(height, 2),
                                "center_z": round(base_z + height / 2.0, 2),
                            }
                        )

    for index, (x_sign, y_sign) in enumerate([(-1, -1), (1, -1), (-1, 1), (1, 1)]):
        marker_size = road_width * 0.75
        x = x_sign * (half - road_width * 0.5)
        y = y_sign * (half - road_width * 0.5)
        terrain_z = footprint_height(x, y, marker_size / 2.0, marker_size / 2.0)
        base_z = terrain_z + 2.0
        add_layout_item(
            layout,
            "markers",
            "PCGGenerated_District_Marker_%02d" % index,
            "building",
            (x, y, base_z + marker_size / 2.0),
            cm_to_cube_scale(marker_size, marker_size, marker_size),
            material_index=index,
            meta={"terrain_z": round(terrain_z, 2), "base_z": round(base_z, 2)},
        )

    return layout


def material_for_layout_item(item, materials, building_materials):
    material_key = item["material_key"]
    if material_key == "building":
        index = item.get("material_index", 0)
        return building_materials[index % len(building_materials)]
    return materials[material_key]


def spawn_city_layout(mesh, materials, layout):
    building_materials = building_material_palette(materials["building"])
    spawned = dict(layout["summary"])
    for group in ("terrain", "roads", "buildings", "markers"):
        for item in layout[group]:
            material = material_for_layout_item(item, materials, building_materials)
            spawn_static_mesh(
                item["label"],
                mesh,
                item["location"],
                item["scale"],
                material,
            )
    return spawned


def save_current_level():
    level_subsystem = get_level_subsystem()
    if level_subsystem is not None:
        try:
            return bool(level_subsystem.save_current_level())
        except Exception:
            pass
    return bool(unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True))


def main():
    level_path = os.environ.get("KNITTEN_UNREAL_LEVEL", DEFAULT_LEVEL)
    blocks = env_int("KNITTEN_UNREAL_CITY_BLOCKS", 4)
    block_size = env_float("KNITTEN_UNREAL_BLOCK_SIZE", 1800.0)
    road_width = env_float("KNITTEN_UNREAL_ROAD_WIDTH", 260.0)
    seed = env_int("KNITTEN_UNREAL_SEED", 7)
    terrain_tiles = env_int("KNITTEN_UNREAL_TERRAIN_TILES", 32)
    road_segments = env_int("KNITTEN_UNREAL_ROAD_SEGMENTS", 24)

    level_state = load_level(level_path)
    deleted = clear_level()
    mesh, mesh_path = cube_mesh()

    terrain_mat, terrain_created = create_solid_material("M_BoxCity_PCG_Terrain", (0.28, 0.38, 0.29), 0.93, 0.08)
    road_mat, road_created = create_solid_material("M_BoxCity_PCG_Road", (0.055, 0.058, 0.064), 0.80, 0.18)
    building_mat, building_created = create_solid_material("M_BoxCity_PCG_Building", (0.44, 0.55, 0.68), 0.78, 0.18)

    graph = create_pcg_graph(
        mesh,
        {
            "terrain": terrain_mat,
            "road": road_mat,
            "building": building_mat,
        },
    )
    pcg_volume, pcg_component = create_context_actors(graph, generate_pcg=False)
    component_summary = instance_summary(pcg_volume)
    city_layout = generate_city_layout(
        blocks=blocks,
        block_size=block_size,
        road_width=road_width,
        seed=seed,
        terrain_tiles=terrain_tiles,
        road_segments=road_segments,
    )
    city_generation = spawn_city_layout(
        mesh,
        {
            "terrain": terrain_mat,
            "road": road_mat,
            "building": building_mat,
        },
        city_layout,
    )
    level_saved = save_current_level()

    summary = {
        "level": level_path,
        "level_state": level_state,
        "deleted_actors": deleted,
        "generator_mode": city_generation["generator"],
        "graph": PCG_GRAPH_PATH,
        "graph_saved": unreal.EditorAssetLibrary.does_asset_exist(PCG_GRAPH_PATH),
        "level_saved": level_saved,
        "mesh": mesh_path,
        "materials": {
            "terrain": {"path": terrain_mat.get_path_name(), "created": terrain_created},
            "road": {"path": road_mat.get_path_name(), "created": road_created},
            "building": {"path": building_mat.get_path_name(), "created": building_created},
        },
        "pcg_volume": pcg_volume.get_actor_label(),
        "pcg_graph_active": bool(pcg_component.get_editor_property("activated")),
        "pcg_generated": bool(pcg_component.get_editor_property("generated")),
        "component_summary": component_summary,
        "city_generation": city_generation,
        "total_actor_count": len(get_all_actors()),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
