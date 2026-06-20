import json
import platform
import sys

import unreal


def has_symbol(name):
    return hasattr(unreal, name)


def editor_subsystem_available(name):
    cls = getattr(unreal, name, None)
    if cls is None:
        return False
    try:
        return unreal.get_editor_subsystem(cls) is not None
    except Exception:
        return False


def main():
    symbols = [
        "EditorActorSubsystem",
        "EditorAssetLibrary",
        "EditorLevelLibrary",
        "EditorLoadingAndSavingUtils",
        "LevelEditorSubsystem",
        "StaticMeshActor",
        "DirectionalLight",
        "SkyLight",
        "PlayerStart",
        "CameraActor",
        "Landscape",
        "LandscapeProxy",
        "LandscapeStreamingProxy",
        "PCGComponent",
    ]

    payload = {
        "python_version": sys.version,
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "engine_version": unreal.SystemLibrary.get_engine_version(),
        "symbols": {name: has_symbol(name) for name in symbols},
        "subsystems": {
            "EditorActorSubsystem": editor_subsystem_available("EditorActorSubsystem"),
            "LevelEditorSubsystem": editor_subsystem_available("LevelEditorSubsystem"),
        },
    }

    print("KNITTEN_UNREAL_PYTHON_PROBE_BEGIN")
    print(json.dumps(payload, indent=2, sort_keys=True))
    print("KNITTEN_UNREAL_PYTHON_PROBE_END")


if __name__ == "__main__":
    main()

