import json
import os

import unreal


DEFAULT_LEVEL = "/Game/Levels/Lvl_MCPPCG"


def vec_to_dict(value):
    return {
        "x": float(value.x),
        "y": float(value.y),
        "z": float(value.z),
    }


def rot_to_dict(value):
    return {
        "pitch": float(value.pitch),
        "yaw": float(value.yaw),
        "roll": float(value.roll),
    }


def load_level(level_path):
    level_subsystem = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if level_subsystem is not None:
        loaded = level_subsystem.load_level(level_path)
        return bool(loaded), "LevelEditorSubsystem.load_level"

    if hasattr(unreal, "EditorLevelLibrary"):
        loaded = unreal.EditorLevelLibrary.load_level(level_path)
        return bool(loaded), "EditorLevelLibrary.load_level"

    return False, "unavailable"


def get_all_level_actors():
    actor_subsystem_cls = getattr(unreal, "EditorActorSubsystem", None)
    if actor_subsystem_cls is not None:
        actor_subsystem = unreal.get_editor_subsystem(actor_subsystem_cls)
        if actor_subsystem is not None:
            return list(actor_subsystem.get_all_level_actors()), "EditorActorSubsystem.get_all_level_actors"

    if hasattr(unreal, "EditorLevelLibrary"):
        return list(unreal.EditorLevelLibrary.get_all_level_actors()), "EditorLevelLibrary.get_all_level_actors"

    return [], "unavailable"


def component_paths(actor, component_cls_name):
    component_cls = getattr(unreal, component_cls_name, None)
    if component_cls is None:
        return []
    try:
        components = actor.get_components_by_class(component_cls)
    except Exception:
        return []
    return [component.get_path_name() for component in components]


def pcg_component_details(actor):
    component_cls = getattr(unreal, "PCGComponent", None)
    if component_cls is None:
        return []
    try:
        components = actor.get_components_by_class(component_cls)
    except Exception:
        return []

    details = []
    for component in components:
        try:
            graph = component.get_graph()
        except Exception:
            graph = None
        details.append(
            {
                "path": component.get_path_name(),
                "graph": graph.get_path_name() if graph is not None else None,
                "generated": bool(component.get_editor_property("generated")),
                "generation_trigger": str(component.get_editor_property("generation_trigger")),
                "seed": int(component.get_editor_property("seed")),
            }
        )
    return details


def mesh_names(actor):
    mesh_component_cls = getattr(unreal, "StaticMeshComponent", None)
    if mesh_component_cls is None:
        return []

    try:
        components = actor.get_components_by_class(mesh_component_cls)
    except Exception:
        return []

    names = []
    for component in components:
        try:
            mesh = component.get_editor_property("static_mesh")
        except Exception:
            mesh = None
        if mesh is not None:
            names.append(mesh.get_path_name())
    return names


def material_names(actor):
    mesh_component_cls = getattr(unreal, "StaticMeshComponent", None)
    if mesh_component_cls is None:
        return []

    try:
        components = actor.get_components_by_class(mesh_component_cls)
    except Exception:
        return []

    names = []
    for component in components:
        try:
            material_count = component.get_num_materials()
        except Exception:
            material_count = 1
        for index in range(material_count):
            try:
                material = component.get_material(index)
            except Exception:
                material = None
            if material is not None:
                names.append(material.get_path_name())
    return names


def actor_to_dict(actor):
    transform = actor.get_actor_transform()
    return {
        "label": actor.get_actor_label(),
        "name": actor.get_name(),
        "class": actor.get_class().get_name(),
        "path": actor.get_path_name(),
        "location": vec_to_dict(transform.translation),
        "rotation": rot_to_dict(transform.rotation.rotator()),
        "scale": vec_to_dict(transform.scale3d),
        "static_meshes": mesh_names(actor),
        "materials": material_names(actor),
        "pcg_components": component_paths(actor, "PCGComponent"),
        "pcg_component_details": pcg_component_details(actor),
    }


def main():
    level_path = os.environ.get("KNITTEN_UNREAL_LEVEL", DEFAULT_LEVEL)
    loaded, load_method = load_level(level_path)
    actors, actor_method = get_all_level_actors()
    actor_data = [actor_to_dict(actor) for actor in actors]
    class_counts = {}
    for actor in actor_data:
        class_counts[actor["class"]] = class_counts.get(actor["class"], 0) + 1

    payload = {
        "level": level_path,
        "loaded": loaded,
        "load_method": load_method,
        "actor_method": actor_method,
        "actor_count": len(actor_data),
        "class_counts": dict(sorted(class_counts.items())),
        "actors": actor_data,
    }

    print("KNITTEN_UNREAL_ACTORS_BEGIN")
    print(json.dumps(payload, indent=2, sort_keys=True))
    print("KNITTEN_UNREAL_ACTORS_END")


if __name__ == "__main__":
    main()
