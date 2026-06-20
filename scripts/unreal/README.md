# Unreal Helper Scripts

This directory collects reusable helper scripts for Unreal MCP and UE Editor
Python experiments. These files are resources for future skill design; they are
not Codex skills and should not contain activation gates.

Baseline used while collecting these scripts:

- Unreal Engine: `/Users/Shared/Epic Games/UE_5.8`
- Test project: `/Users/younsoolim/Documents/UE5d8/Advent/Advent.uproject`
- Observed MCP endpoint: `http://127.0.0.1:8000/mcp`
- Observed test level: `/Game/Levels/Lvl_MCPPCG`

## Scripts

| File | Purpose |
|------|---------|
| `mcp-toolsets.mjs` | List MCP tools and toolsets from a running Unreal Editor MCP server. |
| `probe-remote-execution.py` | Discover PythonScriptPlugin remote execution nodes from outside UE. |
| `refresh-live-level.py` | Ask a running Unreal Editor to reopen a level through Python remote execution. |
| `run-python-commandlet.mjs` | Run a UE Python script through `UnrealEditor-Cmd`. |
| `probe-python.py` | Print UE Python, engine, and editor API availability as JSON. |
| `list-level-actors.py` | Open a level and print actor summaries as JSON without saving. |
| `build-box-city.py` | Create a 4x4 box-only city prototype and save the target level. |
| `randomize-building-materials.py` | Create a color material palette and assign it to box-city buildings. |

## MCP Toolsets

Run this while Unreal Editor is open and its MCP server is listening:

```bash
node scripts/unreal/mcp-toolsets.mjs --url=http://127.0.0.1:8000/mcp
node scripts/unreal/mcp-toolsets.mjs --describe=EditorToolset
node scripts/unreal/mcp-toolsets.mjs --json
```

If the server is not listening, check whether the editor process is running and
whether the Model Context Protocol plugin is enabled for that project.

## Remote Execution Discovery

Run this outside Unreal to check whether the PythonScriptPlugin remote execution
beacon is discoverable:

```bash
python3 scripts/unreal/probe-remote-execution.py
python3 scripts/unreal/probe-remote-execution.py --timeout=5 --bind=127.0.0.1
```

An empty `remote_nodes` list means commandlet scripts are still usable, but live
editor Python execution is not currently discoverable from the client process.
Enable it in Unreal with `Edit > Project Settings > Plugins > Python > Enable
Remote Execution`.

When remote execution is enabled, refresh the open editor by reopening the level:

```bash
python3 scripts/unreal/refresh-live-level.py
python3 scripts/unreal/refresh-live-level.py --level=/Game/Levels/Lvl_MCPPCG --focus
```

## UE Python Commandlet

UE Python scripts can be run through the editor commandlet wrapper. Example:

```bash
node scripts/unreal/run-python-commandlet.mjs \
  --script=scripts/unreal/probe-python.py
```

Read-only actor inventory for the current prototype level:

```bash
KNITTEN_UNREAL_LEVEL=/Game/Levels/Lvl_MCPPCG \
node scripts/unreal/run-python-commandlet.mjs \
  --script=scripts/unreal/list-level-actors.py
```

Box-only city prototype generation:

```bash
KNITTEN_UNREAL_LEVEL=/Game/Levels/Lvl_MCPPCG \
KNITTEN_UNREAL_CITY_BLOCKS=4 \
KNITTEN_UNREAL_BLOCK_SIZE=1800 \
KNITTEN_UNREAL_ROAD_WIDTH=260 \
KNITTEN_UNREAL_SEED=7 \
node scripts/unreal/run-python-commandlet.mjs \
  --script=scripts/unreal/build-box-city.py
```

Randomize building colors:

```bash
KNITTEN_UNREAL_LEVEL=/Game/Levels/Lvl_MCPPCG \
KNITTEN_UNREAL_SEED=17 \
node scripts/unreal/run-python-commandlet.mjs \
  --script=scripts/unreal/randomize-building-materials.py
```

`build-box-city.py` writes and saves the target level. If the live editor is
already open and remote execution is unavailable, reopen or reload the level in
the editor after running the commandlet.

## Environment Variables

| Variable | Used by | Default |
|----------|---------|---------|
| `KNITTEN_UNREAL_ENGINE` | `run-python-commandlet.mjs`, `probe-remote-execution.py` | `/Users/Shared/Epic Games/UE_5.8` |
| `KNITTEN_UNREAL_PROJECT` | `run-python-commandlet.mjs` | `/Users/younsoolim/Documents/UE5d8/Advent/Advent.uproject` |
| `KNITTEN_UNREAL_LEVEL` | `list-level-actors.py`, `build-box-city.py` | `/Game/Levels/Lvl_MCPPCG` |
| `KNITTEN_UNREAL_CITY_BLOCKS` | `build-box-city.py` | `4` |
| `KNITTEN_UNREAL_BLOCK_SIZE` | `build-box-city.py` | `1800` |
| `KNITTEN_UNREAL_ROAD_WIDTH` | `build-box-city.py` | `260` |
| `KNITTEN_UNREAL_SEED` | `build-box-city.py`, `randomize-building-materials.py` | `7` |
| `KNITTEN_UNREAL_COLOR_COUNT` | `randomize-building-materials.py` | `24` |

To pass additional Unreal commandlet flags, use repeated `--editor-arg=...`
options on `run-python-commandlet.mjs`.
