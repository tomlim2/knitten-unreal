# Unreal Reference Pack

This directory is intentionally not a skill payload. It collects source-backed
notes, official documentation links, and local UE 5.8 observations that can be
used later when designing dedicated Unreal skills.

Last refreshed: 2026-06-20

Baseline environment:

- Unreal Engine install: `/Users/Shared/Epic Games/UE_5.8`
- Test project: `/Users/younsoolim/Documents/UE5d8/Advent`
- MCP endpoint observed in editor: `http://127.0.0.1:8000/mcp`

## Documents

| File | Use |
|------|-----|
| `unreal-mcp.md` | Official Unreal MCP setup, Codex config, smoke tests, source anchors, and operational caveats. |
| `ue58-toolsets.md` | UE 5.8 experimental toolset inventory with focus on EditorToolset, PCGToolset, and source locations. |
| `pcg-box-only.md` | Practical PCG notes for asset-free cube prototypes, landscape sampling limits, and future skill workflow shape. |

## Collection Rules

- Treat this folder as research material. Do not put activation gates or skill
  instructions here.
- Before converting a note into a skill, verify the exact engine version,
  enabled plugins, and live `describe_toolset` schema from the running editor.
- Prefer official docs plus local engine source over memory. UE 5.8 MCP and
  Toolset APIs are experimental and can move quickly.
- Keep project-specific observations labeled as observations, not universal
  requirements.

