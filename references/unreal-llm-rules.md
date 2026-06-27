# Unreal LLM Rules

Purpose: minimal text-only context for Unreal tasks. Read this file first. Do
not load the full `references/` directory unless the current task needs deeper
MCP, toolset, PCG, or source-backed details.

Default local paths:

- Knitten Unreal repo: `/Users/younsoolim/Desktop/www/knitten-unreal`
- Unreal project root: `/Users/younsoolim/Documents/UE5d8/Advent`
- Unreal project file: `/Users/younsoolim/Documents/UE5d8/Advent/Advent.uproject`
- Unreal Engine root: `/Users/Shared/Epic Games/UE_5.8`
- Unreal commandlet: `/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd`
- Default test level: `/Game/Levels/Lvl_MCPPCG`
- Default MCP URL: `http://127.0.0.1:8000/mcp`

Default script entry points:

- Run UE Python commandlet: `node scripts/unreal/run-python-commandlet.mjs --script=<script>`
- Probe UE Python: `node scripts/unreal/run-python-commandlet.mjs --script=scripts/unreal/probe-python.py`
- List level actors: `node scripts/unreal/run-python-commandlet.mjs --script=scripts/unreal/list-level-actors.py`
- Build box city: `node scripts/unreal/run-python-commandlet.mjs --script=scripts/unreal/build-box-city.py`
- Randomize box-city building colors: `node scripts/unreal/run-python-commandlet.mjs --script=scripts/unreal/randomize-building-materials.py`
- Legacy post-process conform box city to terrain: `node scripts/unreal/run-python-commandlet.mjs --script=scripts/unreal/conform-city-to-terrain.py`
- Build terrain-aware box city generator: `node scripts/unreal/run-python-commandlet.mjs --script=scripts/unreal/build-pcg-box-city.py`
- Refresh live editor level if Python Remote Execution is enabled: `python3 scripts/unreal/refresh-live-level.py`
- List MCP toolsets: `node scripts/unreal/mcp-toolsets.mjs`

Operational rule:

- Prefer the defaults above unless the user gives a different project, engine,
  level, or MCP endpoint.
- For live editor changes, check MCP or Python remote execution first. If live
  execution is unavailable, commandlet scripts are still valid, but the open
  editor may need the level reloaded.
- For new terrain-aware box-city work, fix `build-pcg-box-city.py` generation
  logic first. Do not use `conform-city-to-terrain.py` as a substitute for
  correcting the generator.
- Treat `build-box-city.py`, `build-pcg-box-city.py`,
  `randomize-building-materials.py`, `conform-city-to-terrain.py`, and similar
  generation scripts as writing scripts; actor inventory and probes are
  read-only.
