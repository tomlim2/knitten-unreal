import json

import unreal


def public_members(obj):
    return [name for name in dir(obj) if not name.startswith("_")]


def main():
    classes = [
        "PCGComponent",
        "PCGSubsystem",
        "PCGEngineSubsystem",
        "PCGBlueprintHelpers",
        "PCGGraph",
        "PCGVolume",
    ]
    payload = {}
    payload["unreal_subsystem_and_tick_symbols"] = [
        name
        for name in public_members(unreal)
        if "subsystem" in name.lower() or "ticker" in name.lower() or name.lower() in ("tick", "sleep")
    ]
    for name in classes:
        cls = getattr(unreal, name, None)
        payload[name] = public_members(cls) if cls is not None else None

    subsystems = {}
    for name in ["PCGSubsystem", "PCGEngineSubsystem"]:
        cls = getattr(unreal, name, None)
        if cls is None:
            subsystems[name] = None
            continue
        try:
            subsystem = unreal.get_editor_subsystem(cls)
        except Exception:
            try:
                subsystem = unreal.get_engine_subsystem(cls)
            except Exception:
                subsystem = None
        subsystems[name] = public_members(subsystem) if subsystem is not None else None
    payload["subsystems"] = subsystems

    print("KNITTEN_UNREAL_PCG_API_BEGIN")
    print(json.dumps(payload, indent=2, sort_keys=True))
    print("KNITTEN_UNREAL_PCG_API_END")


if __name__ == "__main__":
    main()
