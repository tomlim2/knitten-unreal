# PCG Box-Only Prototype Reference

Last refreshed: 2026-06-20

Purpose: keep a practical, asset-free PCG workflow shape for future skills. This
is for experiments that spawn placeholder cubes or boxes first, then swap real
assets later.

## Official References

- PCG overview: https://dev.epicgames.com/documentation/unreal-engine/procedural-content-generation-overview
- PCG framework landing page: https://dev.epicgames.com/documentation/unreal-engine/procedural-content-generation-framework-in-unreal-engine
- PCG node reference: https://dev.epicgames.com/documentation/unreal-engine/procedural-content-generation-framework-node-reference-in-unreal-engine
- PCG data types reference: https://dev.epicgames.com/documentation/unreal-engine/procedural-content-generation-framework-data-types-reference-in-unreal-engine
- PCG generation modes: https://dev.epicgames.com/documentation/unreal-engine/using-pcg-generation-modes-in-unreal-engine
- PCG editor mode: https://dev.epicgames.com/documentation/unreal-engine/pcg-editor-mode-in-unreal-engine
- PCG and Mesh Terrain: https://dev.epicgames.com/documentation/unreal-engine/pcg-and-mesh-terrain-in-unreal-engine?lang=en-US
- Fab in Unreal Engine: https://dev.epicgames.com/documentation/unreal-engine/fab-window-in-unreal-engine

## Plugin Requirements

Enable:

- `ModelContextProtocol`
- `EditorToolset`
- `PCGToolset`

Then start the MCP server and verify `list_toolsets` exposes the PCG and editor
toolsets before attempting graph work.

## Asset-Free Mesh Target

For cube placeholders, use Unreal's built-in cube mesh and verify the required
path shape from the live node schema:

- Package-style path: `/Engine/BasicShapes/Cube`
- Object-style path: `/Engine/BasicShapes/Cube.Cube`

Different tool parameters may ask for a package path, soft object path, object
reference, or asset object. Do not hard-code the form until
`GetNativeNodeSchema("Static Mesh Spawner")` is checked in the running editor.

## Candidate Graph Shape

This is a workflow outline, not a frozen schema:

1. `CreateGraph` in `/Game/PCG`, for example `PCG_BoxScatter`.
2. `ListNativeNodes` with common nodes enabled.
3. `GetNativeNodeSchema` for every node before setting JSON params.
4. Add point source node:
   - `Create Points Grid` for a simple flat prototype.
   - `Surface Sampler` or `Get Landscape Data` when sampling existing surfaces.
5. Add modifiers as needed:
   - `Transform Points`
   - `Spatial Noise`
   - `Self Pruning`
6. Add `Static Mesh Spawner` with the built-in cube mesh.
7. Connect pins with `ConnectNodePins`.
8. Use `GetGraphStructure` to verify graph topology.
9. `SpawnGraphInstance` as a PCG Volume, using the source default scale guidance
   when there is no better reason:

```json
{
  "scale3D": {
    "x": 25,
    "y": 25,
    "z": 10
  }
}
```

10. `ExecuteGraphInstance`.
11. Use `CaptureViewport` from `EditorToolset` to visually verify placement.

## Landscape Notes

Possible with the current PCG surface:

- Sample an existing landscape with PCG nodes such as `Get Landscape Data`.
- Place placeholder cubes on sampled landscape points.
- Use `Projection` or `World Raycast` style workflows to conform points to
  world geometry.

Not directly exposed by the observed MCP toolsets:

- Creating a brand-new Landscape actor.
- Sculpting or painting terrain.
- Managing landscape layers as a dedicated workflow.

There is no `LandscapeToolset` under UE 5.8 `Experimental/Toolsets` in the
observed install. Landscape work should be framed as PCG placement on existing
terrain unless a future custom toolset is authored.

## Data Inspection Safety

`GetNodeDataView` is useful for checking point counts and attributes after graph
execution, but the UE 5.8 source warns that inspection state is shared at the
graph asset level.

For future skills:

- Inspect one PCG actor at a time.
- Wait for `ExecuteGraphInstance` and `GetNodeDataView` to complete before
  inspecting another actor using the same graph.
- Prefer small ranges such as `StartIndex=0`, `EndIndex=20` while debugging.

## When Real Assets Are Needed Later

Box-only tests do not need Fab or Megascans assets.

When moving beyond placeholders, use the Fab window in Unreal or the Epic Games
Launcher to add licensed Unreal-compatible products to the project. Future skills
should treat asset acquisition as a user-owned step unless the user explicitly
asks to install or import assets.

