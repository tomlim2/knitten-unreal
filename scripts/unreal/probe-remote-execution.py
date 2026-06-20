#!/usr/bin/env python3

import argparse
import importlib.util
import json
import os
import pathlib
import sys
import time


DEFAULT_ENGINE = "/Users/Shared/Epic Games/UE_5.8"
DEFAULT_TIMEOUT = 3.0


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
    parser = argparse.ArgumentParser(description="Probe Unreal Python remote execution discovery.")
    parser.add_argument("--engine", default=None, help="Unreal Engine root path.")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="Discovery timeout in seconds.")
    parser.add_argument("--bind", default=None, help="Multicast bind address.")
    parser.add_argument("--group", type=parse_endpoint, default=None, help="Multicast group endpoint host:port.")
    parser.add_argument("--command-endpoint", type=parse_endpoint, default=None, help="Client TCP command endpoint host:port.")
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    engine_root = args.engine or os.environ.get("KNITTEN_UNREAL_ENGINE", DEFAULT_ENGINE)
    module, module_path = load_remote_execution_module(engine_root)

    config = module.RemoteExecutionConfig()
    if args.bind:
        config.multicast_bind_address = args.bind
    if args.group:
        config.multicast_group_endpoint = args.group
    if args.command_endpoint:
        config.command_endpoint = args.command_endpoint

    session = module.RemoteExecution(config)
    started = False
    nodes = []
    error = None
    started_at = time.time()

    try:
        session.start()
        started = True
        deadline = time.monotonic() + max(args.timeout, 0.0)
        while time.monotonic() < deadline:
            nodes = list(session.remote_nodes)
            time.sleep(0.25)
    except Exception as exc:
        error = "%s: %s" % (exc.__class__.__name__, exc)
    finally:
        if started:
            session.stop()

    payload = {
        "engine_root": engine_root,
        "module_path": module_path,
        "timeout": args.timeout,
        "elapsed": round(time.time() - started_at, 3),
        "started": started,
        "error": error,
        "config": {
            "multicast_ttl": config.multicast_ttl,
            "multicast_group_endpoint": list(config.multicast_group_endpoint),
            "multicast_bind_address": config.multicast_bind_address,
            "command_endpoint": list(config.command_endpoint),
        },
        "remote_node_count": len(nodes),
        "remote_nodes": nodes,
    }

    print("KNITTEN_UNREAL_REMOTE_EXECUTION_BEGIN")
    print(json.dumps(payload, indent=2, sort_keys=True))
    print("KNITTEN_UNREAL_REMOTE_EXECUTION_END")
    return 1 if error else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
