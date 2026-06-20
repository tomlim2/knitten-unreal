# Unreal MCP Reference

Last refreshed: 2026-06-20

Purpose: collect the official Unreal MCP setup path, local UE 5.8 source
anchors, and verified connection behavior for future Unreal skill work.

## Official References

- Unreal MCP in Unreal Editor: https://dev.epicgames.com/documentation/unreal-engine/unreal-mcp-in-unreal-editor?lang=en-US
- Unreal MCP plugin API index: https://dev.epicgames.com/documentation/unreal-engine/API/PluginIndex/ModelContextProtocol?lang=en-US
- Unreal AI features landing page: https://dev.epicgames.com/documentation/unreal-engine/ai-features-tools-and-plugins-in-unreal-engine?lang=en-US
- MCP introduction: https://modelcontextprotocol.io/docs/getting-started/intro
- MCP tools spec, 2025-06-18: https://modelcontextprotocol.io/specification/2025-06-18/server/tools
- MCP docs/spec repository: https://github.com/modelcontextprotocol/modelcontextprotocol

## Setup Notes

The plugin identifier is `ModelContextProtocol`; the Plugin Browser friendly
name is `Unreal MCP`.

Enable the plugin through `Edit > Plugins`, search for `Unreal MCP`, and restart
the editor when prompted. The plugin depends on `ToolsetRegistry`.

The MCP server settings are under `Edit > Editor Preferences > General > Model
Context Protocol`. They are not under `Project Settings > Plugins`.

Default endpoint:

```text
http://127.0.0.1:8000/mcp
```

Default project plugin entry:

```json
{
  "Name": "ModelContextProtocol",
  "Enabled": true
}
```

Start manually from the Unreal console:

```text
ModelContextProtocol.StartServer 8000
```

Stop manually:

```text
ModelContextProtocol.StopServer
```

Refresh tool discovery after authoring or hot reload:

```text
ModelContextProtocol.RefreshTools
```

Generate client configuration:

```text
ModelContextProtocol.GenerateClientConfig Codex
```

For Codex, the generated project config is:

```toml
[mcp_servers.unreal-mcp]
url = "http://127.0.0.1:8000/mcp"
```

Official docs note that the Codex TOML config is write-once. If it goes stale,
remove or edit it manually before regenerating.

## Tool Search Behavior

By default, `bEnableToolSearch = true`. In that mode, MCP `tools/list` returns
three meta-tools instead of every Unreal tool:

- `list_toolsets`
- `describe_toolset`
- `call_tool`

Future skills should follow this shape:

1. Call `list_toolsets`.
2. Call `describe_toolset` for the specific toolset.
3. Dispatch the chosen tool through `call_tool`.

Do not assume PCG, Editor, or Actor functions appear directly in `tools/list`.
They appear through the Toolset Registry path when their plugins are enabled.

## Local Source Anchors

| Topic | Local UE 5.8 path | Notes |
|-------|-------------------|-------|
| Plugin descriptor | `/Users/Shared/Epic Games/UE_5.8/Engine/Plugins/Experimental/ModelContextProtocol/ModelContextProtocol.uplugin` | Experimental Unreal MCP plugin. |
| Protocol constants | `/Users/Shared/Epic Games/UE_5.8/Engine/Plugins/Experimental/ModelContextProtocol/Source/ModelContextProtocol/Public/ModelContextProtocol.h` | Default server name `unreal-mcp`, port `8000`, path `/mcp`. Source advertises latest protocol `2025-11-25` and supports `2025-06-18` and `2024-11-05`. |
| Editor preferences settings | `/Users/Shared/Epic Games/UE_5.8/Engine/Plugins/Experimental/ModelContextProtocol/Source/ModelContextProtocolEngine/Public/ModelContextProtocolSettings.h` | `DisplayName="Model Context Protocol"`, config class `EditorPerProjectUserSettings`, default auto-start `false`, default tool search `true`. |
| Server console commands | `/Users/Shared/Epic Games/UE_5.8/Engine/Plugins/Experimental/ModelContextProtocol/Source/ModelContextProtocol/Private/ModelContextProtocolModule.cpp` | Defines `ModelContextProtocol.StartServer` and `ModelContextProtocol.StopServer`. |
| Client config command | `/Users/Shared/Epic Games/UE_5.8/Engine/Plugins/Experimental/ModelContextProtocol/Source/ModelContextProtocolEngine/Private/ModelContextProtocolEngineModule.cpp` | Defines `ModelContextProtocol.GenerateClientConfig <ClaudeCode|Cursor|VSCode|Gemini|Codex|All>`. |
| Codex config target | `/Users/Shared/Epic Games/UE_5.8/Engine/Plugins/Experimental/ModelContextProtocol/Source/ModelContextProtocolEngine/Public/ModelContextProtocolClientConfig.h` | Codex config target is `.codex/config.toml` in the project root. |

## Smoke Test Commands

Check whether Unreal is listening:

```bash
lsof -nP -iTCP:8000 -sTCP:LISTEN
```

Minimal initialize request:

```bash
curl -i -s \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -X POST http://127.0.0.1:8000/mcp \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"codex-smoke","version":"0.0.0"}}}'
```

Expected shape:

- HTTP 200 response.
- `Mcp-Session-Id` response header.
- `serverInfo.name` is `unreal-mcp`.
- Negotiated protocol may be `2025-06-18` when the client requests it, even
  though the UE 5.8 source advertises newer support.

Then send `notifications/initialized`, followed by `tools/list`, using the
session id header returned by initialize.

## Observed Advent State

On 2026-06-20, `/Users/younsoolim/Documents/UE5d8/Advent` had:

- `ModelContextProtocol` enabled in `Advent.uproject`.
- Unreal Editor listening on `127.0.0.1:8000`.
- `.codex/config.toml` pointing at `http://127.0.0.1:8000/mcp`.
- MCP `tools/list` returning only `list_toolsets`, `describe_toolset`, and
  `call_tool`.
- `list_toolsets` returning only `ToolsetRegistry.AgentSkillToolset`, because
  `EditorToolset` and `PCGToolset` were not enabled yet.

## Operational Caveats

- The official docs describe Unreal MCP as experimental; APIs and data formats
  may change.
- The default server is local-only and has no authentication layer. Do not
  expose it beyond loopback.
- Tool invocations are synchronized onto the game thread. Avoid overlapping
  tool calls.
- The editor logs a data/EULA warning when using LLM providers; future skills
  should avoid uploading sensitive project data without user intent.
- If a toolset is missing, first check the project plugin list and then run
  `ModelContextProtocol.RefreshTools` or restart the editor.

