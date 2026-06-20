#!/usr/bin/env python3

import argparse
import importlib.util
import json
import os
import pathlib
import sys
import time


DEFAULT_ENGINE = "/Users/Shared/Epic Games/UE_5.8"
DEFAULT_LEVEL = "/Game/Levels/Lvl_MCPPCG"
DEFAULT_TIMEOUT = 5.0


def parse_endpoint(value):
    host, separator, port = value.rpartition(":")
    if not separator:
        raise argparse.ArgumentTypeError("endpoint must be host:port")
    return host, int(port)


def load_remote_execution_module(engine_root):
    module_path = (
        pathlib.Path(engine_root)
        / "Engine"
        / "Plugins"
        / "Experimental"
        / "PythonScriptPlugin"
        / "Content"
        / "Python"
        / "remote_execution.py"
    )
    if not module_path.exists():
        raise FileNotFoundError(str(module_path))

    spec = importlib.util.spec_from_file_location("ue_remote_execution", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, str(module_path)


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Refresh a running Unreal Editor by reopening a level.")
    parser.add_argument("--engine", default=None, help="Unreal Engine root path.")
    parser.add_argument("--level", default=None, help="Unreal content path to reopen.")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="Discovery timeout in seconds.")
    parser.add_argument("--node-id", default=None, help="Specific remote node id to use.")
    parser.add_argument("--focus", action="store_true", help="Focus the viewport on Landscape_Base_Box or the first actor.")
    parser.add_argument("--bind", default=None, help="Multicast bind address.")
    parser.add_argument("--group", type=parse_endpoint, default=None, help="Multicast group endpoint host:port.")
    parser.add_argument("--command-endpoint", type=parse_endpoint, default=None, help="Client TCP command endpoint host:port.")
    return parser.parse_args(argv)


def build_refresh_command(level_path, focus):
    return r'''
import json
import unreal

level_path = __LEVEL_PATH__
focus = __FOCUS__
level_subsystem = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
loaded = bool(level_subsystem.load_level(level_path))
actors = list(actor_subsystem.get_all_level_actors()) if actor_subsystem else []
focused_actor = None

if loaded and focus and actors:
    target = None
    for actor in actors:
        if actor.get_actor_label() == "Landscape_Base_Box":
            target = actor
            break
    if target is None:
        target = actors[0]
    try:
        level_subsystem.editor_invalidate_viewports()
    except Exception:
        pass
    try:
        unreal.EditorLevelLibrary.pilot_level_actor(target)
        unreal.EditorLevelLibrary.eject_pilot_level_actor()
    except Exception:
        pass
    focused_actor = target.get_actor_label()

payload = {
    "level": level_path,
    "loaded": loaded,
    "actor_count": len(actors),
    "focused_actor": focused_actor,
}
print("KNITTEN_UNREAL_REFRESH_LEVEL_BEGIN")
print(json.dumps(payload, indent=2, sort_keys=True))
print("KNITTEN_UNREAL_REFRESH_LEVEL_END")
'''.replace("__LEVEL_PATH__", repr(level_path)).replace("__FOCUS__", repr(bool(focus)))


def output_payload(payload):
    print("KNITTEN_UNREAL_REFRESH_LEVEL_CLIENT_BEGIN")
    print(json.dumps(payload, indent=2, sort_keys=True))
    print("KNITTEN_UNREAL_REFRESH_LEVEL_CLIENT_END")


def main(argv):
    args = parse_args(argv)
    engine_root = args.engine or os.environ.get("KNITTEN_UNREAL_ENGINE", DEFAULT_ENGINE)
    level_path = args.level or os.environ.get("KNITTEN_UNREAL_LEVEL", DEFAULT_LEVEL)
    module, module_path = load_remote_execution_module(engine_root)

    config = module.RemoteExecutionConfig()
    if args.bind:
        config.multicast_bind_address = args.bind
    if args.group:
        config.multicast_group_endpoint = args.group
    if args.command_endpoint:
        config.command_endpoint = args.command_endpoint

    session = module.RemoteExecution(config)
    started_at = time.time()
    exit_code = 0
    client_payload = {
        "engine_root": engine_root,
        "level": level_path,
        "module_path": module_path,
        "timeout": args.timeout,
        "remote_node_count": 0,
        "selected_node_id": None,
        "success": False,
        "error": None,
        "remote_output": "",
        "hint": None,
    }

    try:
        session.start()
        deadline = time.monotonic() + max(args.timeout, 0.0)
        nodes = list(session.remote_nodes)
        while not nodes and time.monotonic() < deadline:
            time.sleep(0.25)
            nodes = list(session.remote_nodes)

        client_payload["remote_node_count"] = len(nodes)
        if not nodes:
            client_payload["hint"] = (
                "Enable Unreal Python Remote Execution: "
                "Edit > Project Settings > Plugins > Python > Enable Remote Execution"
            )
            exit_code = 2
            return exit_code, client_payload

        selected = None
        if args.node_id:
            for node in nodes:
                if node.get("node_id") == args.node_id:
                    selected = node
                    break
            if selected is None:
                client_payload["error"] = "requested node id was not found"
                exit_code = 3
                return exit_code, client_payload
        else:
            selected = nodes[0]

        node_id = selected["node_id"]
        client_payload["selected_node_id"] = node_id
        session.open_command_connection(node_id)
        result = session.run_command(
            build_refresh_command(level_path, args.focus),
            exec_mode=module.MODE_EXEC_FILE,
            raise_on_failure=False,
        )
        output = "".join(item.get("output", "") for item in result.get("output", []))
        client_payload["remote_output"] = output
        client_payload["success"] = bool(result.get("success"))
        if not client_payload["success"]:
            client_payload["error"] = result.get("result") or "remote command failed"
            exit_code = 4
    except Exception as exc:
        client_payload["error"] = "%s: %s" % (exc.__class__.__name__, exc)
        exit_code = 1
    finally:
        try:
            session.close_command_connection()
        except Exception:
            pass
        session.stop()
        client_payload["elapsed"] = round(time.time() - started_at, 3)

    return exit_code, client_payload


if __name__ == "__main__":
    code, payload = main(sys.argv[1:])
    output_payload(payload)
    raise SystemExit(code)

