# UE 5.8 Toolsets Reference

Last refreshed: 2026-06-20

Purpose: map the installed UE 5.8 experimental Toolset plugins and identify
which ones matter most for future editor-control and PCG skills.

## Official References

- Unreal MCP Toolset Registry section: https://dev.epicgames.com/documentation/unreal-engine/unreal-mcp-in-unreal-editor?lang=en-US
- PCGToolset API index: https://dev.epicgames.com/documentation/unreal-engine/API/PluginIndex/PCGToolset?lang=en-US
- ModelContextProtocol API index: https://dev.epicgames.com/documentation/unreal-engine/API/PluginIndex/ModelContextProtocol?lang=en-US

## Core Plugin Map

| Plugin | Local path | Role |
|--------|------------|------|
| `ModelContextProtocol` | `/Users/Shared/Epic Games/UE_5.8/Engine/Plugins/Experimental/ModelContextProtocol/ModelContextProtocol.uplugin` | Hosts the MCP server in Unreal. |
| `ToolsetRegistry` | `/Users/Shared/Epic Games/UE_5.8/Engine/Plugins/Experimental/ToolsetRegistry/ToolsetRegistry.uplugin` | Discovers reflected toolsets and backs Unreal MCP tool exposure. Depends on Python, Editor Scripting Utilities, and FileSandbox. |
| `EditorToolset` | `/Users/Shared/Epic Games/UE_5.8/Engine/Plugins/Experimental/Toolsets/EditorToolset/EditorToolset.uplugin` | Editor state, selection, viewport/camera, asset thumbnails, content browser, and PIE control. |
| `PCGToolset` | `/Users/Shared/Epic Games/UE_5.8/Engine/Plugins/Experimental/Toolsets/PCGToolset/PCGToolset.uplugin` | Create, modify, spawn, execute, and inspect PCG graphs. Depends on `PCG` and `ToolsetRegistry`. |
| `AllToolsets` | `/Users/Shared/Epic Games/UE_5.8/Engine/Plugins/Experimental/Toolsets/AllToolsets/AllToolsets.uplugin` | Aggregator plugin that enables many toolset plugins for exploration. Use narrower plugin enablement for repeatable skills. |
| `MCPClientToolset` | `/Users/Shared/Epic Games/UE_5.8/Engine/Plugins/Experimental/Toolsets/MCPClientToolset/MCPClientToolset.uplugin` | Adapter for Unreal/toolset consumers to connect to local/private MCP servers. This is Unreal as MCP client, not Codex connecting to Unreal. |

## Project Enablement Snippets

Minimum server:

```json
{
  "Name": "ModelContextProtocol",
  "Enabled": true
}
```

Practical editor and PCG control:

```json
{
  "Name": "EditorToolset",
  "Enabled": true
},
{
  "Name": "PCGToolset",
  "Enabled": true
}
```

Exploration-only broad enablement:

```json
{
  "Name": "AllToolsets",
  "Enabled": true
}
```

Prefer explicit `EditorToolset` and `PCGToolset` entries for skills that need
repeatable setup. `AllToolsets` is useful for discovery, but it expands the
surface area and may enable unrelated experimental systems.

## Local Toolset Inventory

The installed UE 5.8 `Experimental/Toolsets` directory contains:

- `AIModuleToolset`
- `AllToolsets`
- `AnimationAssistantToolset`
- `AutomationTestToolset`
- `ChaosClothAssetToolset`
- `ConfigSettingsToolset`
- `ConversationToolset`
- `DataRegistryToolset`
- `DataflowAgent`
- `EditorToolset`
- `GASToolsets`
- `GameFeaturesToolset`
- `GameplayTagsToolset`
- `LiveCodingToolset`
- `MCPClientToolset`
- `MVVMToolset`
- `MetaHumanGenerator`
- `NiagaraToolsets`
- `PCGToolset`
- `PhysicsToolsets`
- `PluginToolset`
- `SemanticSearchToolset`
- `SequencerAnimMixerToolset`
- `SlateInspectorToolset`
- `StateTreeToolset`
- `UMGToolSet`
- `WorldConditionsToolset`

`AllToolsets` aggregates many, but not necessarily every, directory in this
install. Check the local `AllToolsets.uplugin` before assuming coverage.

## EditorToolset Surface

Source:

```text
/Users/Shared/Epic Games/UE_5.8/Engine/Plugins/Experimental/Toolsets/EditorToolset/Source/EditorToolset/Private/EditorAppToolset.h
```

Useful `AICallable` functions include:

- `SearchCVars`
- `CaptureAssetImage`
- `CaptureEditorImage`
- `CaptureViewport`
- `GetSelectedActors`
- `SelectActors`
- `GetCameraTransform`
- `SetCameraTransform`
- `FocusOnActors`
- `GetVisibleActors`
- `WorldPosToScreenCoords`
- `ScreenCoordsToWorld`
- `GetSelectedAssets`
- `SelectAssets`
- `GetContentBrowserPath`
- `SetContentBrowserPath`
- `OpenEditorForAsset`
- `GetOpenAssets`
- `StartPIE`
- `StopPIE`
- `IsPIERunning`

Future skills can use this as the verification and visual-feedback layer around
PCG or level-building workflows.

## PCGToolset Surface

Source:

```text
/Users/Shared/Epic Games/UE_5.8/Engine/Plugins/Experimental/Toolsets/PCGToolset/Source/PCGToolset/Public/PCGToolset.h
```

Useful `AICallable` groups:

- Graph assets: `CreateGraph`
- Graph schema and parameters: `GetGraphStructure`, `SetGraphParams`,
  `RemoveGraphParams`, `GetGraphSchema`, `GetGraphDescription`,
  `SetGraphDescription`
- Instances: `ListGraphInstances`, `SpawnGraphInstance`,
  `ExecuteGraphInstance`
- Instance params: `GetGraphInstanceParams`, `SetGraphInstanceParams`,
  `ResetGraphInstanceParams`
- Native node discovery: `ListNativeNodes`, `ListAvailableSubgraphs`,
  `GetNativeNodeSchema`
- Node editing: `AddNode`, `AddSubgraphNode`, `UpdateNode`,
  `SetNodeComment`, `GetNodeInfo`, `RepositionNode`, `RemoveNode`,
  `ConnectNodePins`, `DisconnectNodePins`
- Data inspection: `GetNodeDataView`
- Comment boxes: `AddCommentBox`, `UpdateCommentBox`, `RemoveCommentBox`
- Viewport-assisted spline input: `DrawSpline`

Spatial source:

```text
/Users/Shared/Epic Games/UE_5.8/Engine/Plugins/Experimental/Toolsets/PCGToolset/Source/PCGToolset/Public/PCGSpatialToolset.h
```

This exposes `RunPCGInstantGraph`.

Important inspection warning from `GetNodeDataView`: inspection state is shared
at the graph asset level. For actors using the same graph, call data inspection
and graph execution on only one actor at a time.

## Common PCG Native Nodes

Source:

```text
/Users/Shared/Epic Games/UE_5.8/Engine/Plugins/Experimental/Toolsets/PCGToolset/Source/PCGToolset/Public/PCGToolsetLibraryCore.h
```

Common node names include:

- `Create Points`
- `Create Points Grid`
- `Get Actor Data`
- `Get Landscape Data`
- `Get Spline Data`
- `Get Texture Data`
- `Get Volume Data`
- `Point From Mesh`
- `Projection`
- `Self Pruning`
- `Spatial Noise`
- `Static Mesh Spawner`
- `Surface Sampler`
- `Transform Points`
- `Volume Sampler`
- `World Raycast`

Always call `GetNativeNodeSchema` for exact parameters before generating a graph.

## Landscape-Adjacent Plugins

There is no dedicated `LandscapeToolset` in this UE 5.8 install under
`Experimental/Toolsets`.

Related non-MCP-toolset plugins:

- `LandscapePatch`: `/Users/Shared/Epic Games/UE_5.8/Engine/Plugins/Editor/LandscapePatch/LandscapePatch.uplugin`
- `MeshTerrainMode`: `/Users/Shared/Epic Games/UE_5.8/Engine/Plugins/Experimental/MeshTerrainMode/MeshTerrainMode.uplugin`

PCG can sample landscape data through PCG nodes such as `Get Landscape Data`,
but direct landscape sculpt/paint workflows are not exposed as a dedicated MCP
toolset in this install.

