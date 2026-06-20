"""
Send a Python script to a running UE Editor instance for remote execution.

Usage:
    python run_in_editor.py <script_path>
    python run_in_editor.py --code "print('hello')"
    python run_in_editor.py --list-nodes

Requires UE Editor running with Python Remote Execution enabled.
"""

import sys
import os
import time
import argparse

# Add UE's Python plugin to path so we can import remote_execution
def _get_ue_plugin_path():
    import json
    config = os.path.join(os.path.expanduser("~"), ".agent-local", "private", "agent-hub-config", "machine-paths.json")
    try:
        with open(config) as _f:
            _ue_root = json.load(_f).get("unreal-editor", "")
        if _ue_root:
            return os.path.join(_ue_root, "Engine", "Plugins", "Experimental",
                                "PythonScriptPlugin", "Content", "Python")
    except (FileNotFoundError, KeyError, ValueError):
        pass
    return None

_ue_plugin_path = _get_ue_plugin_path()
if _ue_plugin_path and os.path.isdir(_ue_plugin_path) and _ue_plugin_path not in sys.path:
    sys.path.insert(0, _ue_plugin_path)

import remote_execution


def discover_nodes(timeout=3.0):
    """Start discovery and wait for UE Editor nodes."""
    remote_exec = remote_execution.RemoteExecution()
    remote_exec.start()

    deadline = time.time() + timeout
    while time.time() < deadline:
        nodes = remote_exec.remote_nodes
        if nodes:
            return remote_exec, nodes
        time.sleep(0.2)

    remote_exec.stop()
    return None, []


def run_script(script_path):
    """Send a script file path to UE Editor for execution.

    UE's ExecuteFile mode can load a file by path directly,
    which is more reliable than sending the file content as a string.
    """
    abs_path = os.path.abspath(script_path)
    if not os.path.isfile(abs_path):
        print(f"Error: Script not found: {abs_path}", file=sys.stderr)
        return False

    # Send the file path - UE will load and execute it
    return _execute(abs_path, exec_mode=remote_execution.MODE_EXEC_FILE)


def run_code(code):
    """Send inline Python code to UE Editor for execution."""
    return _execute(code, exec_mode=remote_execution.MODE_EXEC_FILE)


def _execute(command, exec_mode):
    """Connect to UE Editor and execute a command."""
    print("Discovering UE Editor...", file=sys.stderr)
    remote_exec, nodes = discover_nodes()

    if not nodes:
        print("Error: No UE Editor instances found. Is Python Remote Execution enabled?", file=sys.stderr)
        return False

    node = nodes[0]
    node_id = node["node_id"]
    project = node.get("project_name", "Unknown")
    print(f"Found: {project} (node: {node_id[:8]}...)", file=sys.stderr)

    try:
        remote_exec.open_command_connection(node_id)
        print("Connected. Executing...", file=sys.stderr)

        result = remote_exec.run_command(command, exec_mode=exec_mode)

        success = result.get("success", False)
        output = result.get("result", "")
        log_lines = result.get("output", [])

        if log_lines:
            for line in log_lines:
                line_type = line.get("type", "Info")
                line_text = line.get("output", "")
                print(f"[{line_type}] {line_text}")

        if output:
            print(output)

        if success:
            print("Execution completed successfully.", file=sys.stderr)
        else:
            print(f"Execution failed: {output}", file=sys.stderr)

        return success

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return False

    finally:
        remote_exec.stop()


def list_nodes():
    """List discovered UE Editor instances."""
    print("Discovering UE Editor instances...", file=sys.stderr)
    remote_exec, nodes = discover_nodes(timeout=5.0)

    if not nodes:
        print("No UE Editor instances found.")
        if remote_exec:
            remote_exec.stop()
        return

    for node in nodes:
        print(f"  Node: {node.get('node_id', 'unknown')[:8]}...")
        print(f"  Project: {node.get('project_name', 'N/A')}")
        print(f"  Engine: {node.get('engine_version', 'N/A')}")
        print(f"  User: {node.get('user', 'N/A')}@{node.get('machine', 'N/A')}")
        print()

    remote_exec.stop()


def main():
    parser = argparse.ArgumentParser(description="Execute Python in UE Editor remotely")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("script", nargs="?", help="Path to Python script to execute")
    group.add_argument("--code", "-c", help="Python code string to execute")
    group.add_argument("--list-nodes", "-l", action="store_true", help="List discovered UE Editor instances")

    args = parser.parse_args()

    if args.list_nodes:
        list_nodes()
    elif args.code:
        success = run_code(args.code)
        sys.exit(0 if success else 1)
    elif args.script:
        success = run_script(args.script)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
