---
status: accepted
domains: unreal
repo-keys: anju,mega-melange
languages: cpp,python
task-types: implementation,review
context-profile: unreal-engine
exclude-when: rust,web,obsidian
---
# Unreal Engine Asset Naming Conventions

**Version:** 0.1.0

## Changelog

- **0.1.0** - Initial release

---

## Philosophy

### Why Asset Naming Matters

Consistent asset naming is not just about aesthetics—it's fundamental to team collaboration, automated pipelines, and project maintainability.

**Benefits:**
- **Instant Recognition**: Know what an asset is without opening it
- **Alphabetical Grouping**: Related assets cluster together in Content Browser
- **Search Efficiency**: Find assets quickly using prefix/suffix filters
- **Automation-Friendly**: Scripts can process assets by naming patterns
- **Reduced Errors**: Clear ownership and type prevent accidental misuse
- **Team Scalability**: New team members onboard faster with predictable naming

**Cost of Inconsistency:**
- Time wasted searching for assets
- Duplicate assets created unknowingly
- Broken references during renames
- Confusion about asset purpose/state
- Automation scripts break on edge cases

---

## Core Naming Rules

All Unreal Engine assets **MUST** follow these 9 rules:

| # | Rule | Severity | Description |
|---|------|----------|-------------|
| 1 | `ASCII_ONLY` | **ERROR** | No non-ASCII characters (e.g. Korean, CJK, emoji) |
| 2 | `ALLOWED_CHARS` | **ERROR** | Only `[A-Za-z0-9_]` allowed (no spaces, hyphens, dots) |
| 3 | `NO_DOUBLE_UNDERSCORE` | WARN | No consecutive `__` |
| 4 | `NO_TRAILING_UNDERSCORE` | WARN | Name must not end with `_` |
| 5 | `PREFIX` | **ERROR** | Correct type prefix (e.g. `SM_`, `T_`, `M_`) |
| 6 | `PASCAL_CASE` | WARN | Each segment starts uppercase |
| 7 | `ZERO_PADDED_NUMBER` | WARN | Variant numbers use 2-digit padding (`_01`, `_02`) |
| 8 | `TEXTURE_SUFFIX` | WARN | Textures should have channel suffix (e.g. `_D`, `_N`) |
| 9 | `SOUND_CUE_SUFFIX` | WARN | SoundCue should end with `_Cue` |

### Rule Details

#### 1. ASCII_ONLY (ERROR)

**Rule:** Asset names must use only ASCII characters (A-Z, a-z, 0-9, underscore).

**Why:**
- Cross-platform compatibility (Windows/Mac/Linux file systems)
- Version control systems (Git) handle ASCII better
- Build automation and CI/CD pipelines expect ASCII
- Some UE Python APIs fail on non-ASCII paths

```
❌ BAD:
M_캐릭터_머리카락           # Korean characters
SM_箱子                    # Chinese characters
T_Diffuse★                 # Emoji/special symbols

✅ GOOD:
M_Character_Hair
SM_Box
T_Diffuse
```

**CJK Assets:** If you have assets with CJK names, use `/ue-validate-asset-name` to get translation suggestions. Translate literally (e.g., `下擺` → `Hem`), don't add context that isn't in the original name.

#### 2. ALLOWED_CHARS (ERROR)

**Rule:** Only letters, numbers, and underscores. No spaces, hyphens, dots, or special characters.

**Why:**
- Spaces break command-line tools and scripts
- Hyphens cause ambiguity (is it negative number?)
- Dots conflict with file extensions
- Special chars break regex patterns

```
❌ BAD:
SM_Character-Hair          # Hyphen
T_Rock Diffuse             # Space
MI_Material.Instance       # Dot
BP_Player#1                # Hash

✅ GOOD:
SM_Character_Hair
T_RockDiffuse
MI_MaterialInstance
BP_Player_01
```

#### 3. NO_DOUBLE_UNDERSCORE (WARN)

**Rule:** Avoid consecutive underscores `__`.

**Why:**
- Looks like typo/mistake
- Some systems use `__` for special purposes (Python name mangling)
- Reduces readability

```
❌ BAD:
SM_Character__Hair
T_Rock__Diffuse

✅ GOOD:
SM_Character_Hair
T_RockDiffuse
```

#### 4. NO_TRAILING_UNDERSCORE (WARN)

**Rule:** Names must not end with underscore.

**Why:**
- Suggests incomplete name
- Inconsistent with naming patterns

```
❌ BAD:
SM_Character_
T_Rock_Diffuse_

✅ GOOD:
SM_Character
T_Rock_Diffuse
```

#### 5. PREFIX (ERROR)

**Rule:** All assets must start with the correct type prefix.

**Why:**
- Instant type recognition in Content Browser
- Alphabetical grouping by type
- Blueprint variables auto-suggest correct prefix
- Prevents naming conflicts between types

See **Prefix Table** below for complete list.

```
❌ BAD:
Character              # No prefix (is it mesh? blueprint? skeleton?)
M_PlayerMesh           # Wrong prefix (mesh should be SM_ or SK_)
Texture_Diffuse        # Wrong prefix (should be T_)

✅ GOOD:
SK_Character           # Skeletal mesh
M_Player               # Material
T_Diffuse              # Texture
```

#### 6. PASCAL_CASE (WARN)

**Rule:** Each underscore-separated segment should start with uppercase letter.

**Why:**
- Consistent with Unreal's C++ naming (PascalCase)
- Improves readability
- Matches Epic's official assets

```
❌ BAD:
SM_character_hair      # All lowercase
T_rock_diffuse         # All lowercase
M_playerMaterial       # camelCase

✅ GOOD:
SM_Character_Hair
T_Rock_Diffuse
M_PlayerMaterial       # But prefer: M_Player_Material
```

#### 7. ZERO_PADDED_NUMBER (WARN)

**Rule:** Variant numbers should be zero-padded to 2 digits for <100 variants.

**Why:**
- Correct alphabetical sorting (01, 02, ..., 10 instead of 1, 10, 2)
- Consistent digit width
- Easier to scan visually

```
❌ BAD:
SM_Rock_1              # Not padded
SM_Rock_2
SM_Rock_10             # Sorts incorrectly (1, 10, 2)

SM_Rock_001            # Over-padded for <100 variants
SM_Rock_002

✅ GOOD:
SM_Rock_01
SM_Rock_02
SM_Rock_10             # Sorts correctly (01, 02, ..., 10)
```

#### 8. TEXTURE_SUFFIX (WARN)

**Rule:** Textures should indicate their channel/purpose with a suffix.

**Why:**
- Identify texture type without opening
- Group related textures together
- Material editor knows which texture to use

See **Texture Suffix Table** below for complete list.

```
❌ BAD:
T_Rock                 # What channel? Diffuse? Normal?
T_Character            # Too vague

✅ GOOD:
T_Rock_D               # Diffuse/BaseColor
T_Rock_N               # Normal
T_Rock_R               # Roughness
T_Character_BC         # BaseColor
T_Character_ORM        # Packed (Occlusion+Roughness+Metallic)
```

#### 9. SOUND_CUE_SUFFIX (WARN)

**Rule:** SoundCue assets should end with `_Cue`.

**Why:**
- Distinguish from SoundWave assets (both use `A_` prefix)
- Follow Epic's convention
- Prevent accidental direct SoundWave references

```
❌ BAD:
A_Explosion            # Is this Wave or Cue?
A_Footstep

✅ GOOD:
A_Explosion_Cue        # Clearly a SoundCue
A_Footstep             # SoundWave (no _Cue suffix)
```

---

## Prefix Table

Based on Epic's official conventions and Allar's community standard.

### Meshes

| Type | Prefix | Example |
|------|--------|---------|
| StaticMesh | `SM_` | `SM_Rock_01` |
| SkeletalMesh | `SK_` | `SK_Character` |

### Animations

| Type | Prefix | Example |
|------|--------|---------|
| AnimSequence | `AS_` | `AS_Character_Idle` |
| AnimMontage | `AM_` | `AM_Character_Attack` |
| AnimBlueprint | `ABP_` | `ABP_Character` |
| BlendSpace | `BS_` | `BS_Character_Walk` |
| BlendSpace1D | `BS_` | `BS_Character_Speed` |
| AimOffsetBlendSpace | `AO_` | `AO_Character_Aim` |
| AimOffsetBlendSpace1D | `AO_` | `AO_Character_Pitch` |

### Materials

| Type | Prefix | Example |
|------|--------|---------|
| Material | `M_` | `M_Character_Body` |
| MaterialInstanceConstant | `MI_` | `MI_Character_Body_Blue` |
| MaterialFunction | `MF_` | `MF_TintColor` |
| MaterialParameterCollection | `MPC_` | `MPC_GlobalParams` |
| SubsurfaceProfile | `SSP_` | `SSP_Skin` |
| PhysicalMaterial | `PM_` | `PM_Metal` |

### Textures

| Type | Prefix | Example |
|------|--------|---------|
| Texture2D | `T_` | `T_Rock_D`, `T_Rock_N` |
| TextureCube | `TC_` | `TC_Sky` |
| TextureRenderTarget2D | `RT_` | `RT_SceneCapture` |
| MediaTexture | `MT_` | `MT_Video` |

### Blueprints

| Type | Prefix | Example |
|------|--------|---------|
| Blueprint (e.g. Actor, Component) | `BP_` | `BP_Player`, `BP_Door` |
| WidgetBlueprint (UMG) | `WBP_` | `WBP_MainMenu`, `WBP_HUD` |

### Particles / VFX

| Type | Prefix | Example |
|------|--------|---------|
| NiagaraSystem | `FXS_` | `FXS_Explosion` |
| NiagaraEmitter | `FXE_` | `FXE_Sparks` |
| NiagaraParameterCollection | `FXC_` | `FXC_GlobalVFX` |
| ParticleSystem (Cascade, legacy) | `PS_` | `PS_Fire` |

### Sounds

| Type | Prefix | Example |
|------|--------|---------|
| SoundWave | `A_` | `A_Footstep`, `A_Gunshot` |
| SoundCue | `A_` | `A_Explosion_Cue` (note `_Cue` suffix) |

### Physics

| Type | Prefix | Example |
|------|--------|---------|
| PhysicsAsset | `PHYS_` | `PHYS_Character` |

### Skeletons

| Type | Prefix | Example |
|------|--------|---------|
| Skeleton | `SKEL_` | `SKEL_Character` |

### Data Assets

| Type | Prefix | Example |
|------|--------|---------|
| DataTable | `DT_` | `DT_Items`, `DT_Quests` |
| CurveFloat | `Curve_` | `Curve_DamageOverTime` |
| CurveVector | `Curve_` | `Curve_MovementPath` |
| CurveLinearColor | `Curve_` | `Curve_ColorFade` |

### AI

| Type | Prefix | Example |
|------|--------|---------|
| BehaviorTree | `BT_` | `BT_Enemy` |
| BlackboardData | `BB_` | `BB_Enemy` |
| EnvironmentQuery | `EQS_` | `EQS_FindCover` |

### UI

| Type | Prefix | Example |
|------|--------|---------|
| Font | `Font_` | `Font_Roboto` |
| SlateBrushAsset | `Brush_` | `Brush_Button` |
| SlateWidgetStyleAsset | `Style_` | `Style_Button` |

### Maps / Levels

| Type | Prefix | Example |
|------|--------|---------|
| World (Map) | *(no prefix)* | `MainMenu`, `Level_01_Forest` |
| MapBuildDataRegistry | *(no prefix)* | *(auto-generated)* |

---

## Texture Suffix Table

Texture2D assets should include a channel/purpose suffix **before** any variant number.

### Single Channel Textures

| Suffix | Meaning | Common Usage |
|--------|---------|--------------|
| `_D` | Diffuse / Albedo | Legacy term, same as BaseColor |
| `_BC` | BaseColor | PBR standard, RGB color without lighting |
| `_N` | Normal | Tangent-space normal map (RGB) |
| `_R` | Roughness | Surface roughness (grayscale) |
| `_M` | Metallic | Metallic mask (grayscale) |
| `_MT` | Metallic | Alternative suffix for Metallic |
| `_S` | Specular | Specular intensity (grayscale, legacy) |
| `_AO` | Ambient Occlusion | Cavity shadows (grayscale) |
| `_O` | Occlusion | Short form of AO |
| `_E` | Emissive | Self-illumination (RGB or grayscale) |
| `_A` | Alpha / Opacity | Transparency mask (grayscale) |
| `_H` | Height | Heightmap for parallax/displacement |
| `_B` | Bump | Bump map (legacy, use Normal instead) |
| `_DP` | Displacement | Geometric displacement |
| `_FM` | FlowMap | Vector flow direction (RG) |
| `_L` | LightMap | Baked lighting (RGB) |

### Packed Channel Textures

UE often packs multiple grayscale channels into one RGB(A) texture for performance.

| Suffix | Channels | Description |
|--------|----------|-------------|
| `_ORM` | R=AO, G=Roughness, B=Metallic | Standard UE5 packed texture |
| `_ORA` | R=AO, G=Roughness, B=Unused, A=Alpha | With transparency |
| `_MRA` | R=Metallic, G=Roughness, B=Unused, A=Alpha | Alternative packing |
| `_MRO` | R=Metallic, G=Roughness, B=AO | Alternative order |

### Examples

```
✅ GOOD:
T_Rock_D              # Diffuse only
T_Rock_N              # Normal map
T_Rock_ORM            # Packed (Occlusion+Roughness+Metallic)
T_Rock_E              # Emissive

T_Character_BC        # BaseColor
T_Character_N         # Normal
T_Character_R         # Roughness
T_Character_M         # Metallic

T_Foliage_BC_01       # BaseColor, variant 01
T_Foliage_N_01        # Normal, variant 01

❌ BAD:
T_Rock                # Missing suffix
T_Character           # Missing suffix
T_Texture_Diffuse     # Verbose, inconsistent
```

---

## Complete Naming Pattern

```
[Prefix]_[BaseName]_[OptionalVariant]_[OptionalSuffix]_[OptionalNumber]

Prefix:          Type prefix (SM_, T_, M_, etc.)
BaseName:        Descriptive name in PascalCase
OptionalVariant: Variant identifier (Color, LOD, etc.)
OptionalSuffix:  Channel/purpose suffix (textures only)
OptionalNumber:  Zero-padded variant number (01, 02, etc.)
```

### Examples by Asset Type

#### Static Meshes
```
SM_Rock_01
SM_Rock_02
SM_Tree_Pine_LOD0
SM_Building_House_01
SM_Prop_Chair
```

#### Skeletal Meshes
```
SK_Character_Hero
SK_Character_Enemy_Goblin
SK_Weapon_Sword
```

#### Materials
```
M_Character_Skin
M_Rock_Granite
M_Metal_Rusty
M_Glass_Clear
```

#### Material Instances
```
MI_Character_Skin_PaleBlue
MI_Rock_Granite_Wet
MI_Metal_Rusty_Red
```

#### Textures
```
T_Rock_BC                  # BaseColor
T_Rock_N                   # Normal
T_Rock_ORM                 # Packed

T_Character_BC_01          # BaseColor, variant 01
T_Character_N_01           # Normal, variant 01

T_UI_Button_Idle_D         # UI texture, Diffuse
T_UI_Button_Hover_D
```

#### Blueprints
```
BP_Player
BP_Enemy_Goblin
BP_Pickup_HealthPack
BP_Weapon_Rifle
```

#### Widgets
```
WBP_MainMenu
WBP_HUD
WBP_InventorySlot
WBP_HealthBar
```

#### Animations
```
AS_Character_Idle
AS_Character_Walk
AS_Character_Attack_01
AM_Character_Combo
ABP_Character
```

#### Sounds
```
A_Footstep_Grass           # SoundWave
A_Footstep_Metal           # SoundWave
A_Explosion_Cue            # SoundCue (note _Cue suffix)
A_Music_Combat_Cue         # SoundCue
```

#### VFX
```
FXS_Explosion
FXS_Fire
FXE_Sparks
FXE_Smoke
```

---

## Common Mistakes

### ❌ Mistake 1: No Prefix
```
❌ BAD:
Character              # What type is this?
Rock
Texture_Diffuse        # Wrong prefix format

✅ GOOD:
SK_Character
SM_Rock
T_Diffuse
```

### ❌ Mistake 2: Wrong Prefix
```
❌ BAD:
M_CharacterMesh        # Material prefix on mesh name
SM_PlayerMaterial      # Mesh prefix on material name
T_Material_Diffuse     # Texture prefix, but name suggests material

✅ GOOD:
SK_Character
M_Player
T_Diffuse
```

### ❌ Mistake 3: Inconsistent Capitalization
```
❌ BAD:
SM_character_hair      # All lowercase
T_ROCK_DIFFUSE         # All uppercase
M_playerMaterial       # camelCase

✅ GOOD:
SM_Character_Hair
T_Rock_Diffuse
M_Player_Material
```

### ❌ Mistake 4: Spaces and Special Characters
```
❌ BAD:
SM_Character Hair      # Space
T_Rock-Diffuse         # Hyphen
MI_Material.Blue       # Dot

✅ GOOD:
SM_Character_Hair
T_Rock_Diffuse
MI_Material_Blue
```

### ❌ Mistake 5: Non-ASCII Characters
```
❌ BAD:
M_캐릭터_머리
SM_キャラクター
T_岩石_Diffuse

✅ GOOD:
M_Character_Hair
SM_Character
T_Rock_Diffuse
```

### ❌ Mistake 6: Missing Texture Suffix
```
❌ BAD:
T_Rock                 # Which channel?
T_Character            # Diffuse? Normal?

✅ GOOD:
T_Rock_D               # or T_Rock_BC
T_Rock_N
T_Character_BC
T_Character_N
```

### ❌ Mistake 7: Unpadded Variant Numbers
```
❌ BAD:
SM_Rock_1              # Sorts incorrectly
SM_Rock_2
SM_Rock_10             # 1, 10, 2 (wrong order)

✅ GOOD:
SM_Rock_01
SM_Rock_02
SM_Rock_10             # 01, 02, 10 (correct order)
```

---

## CJK Asset Handling

### Problem

Assets with Korean, Chinese, or Japanese names violate the `ASCII_ONLY` rule and cause issues:
- UE Python API failures (`rename_asset()` returns `False`)
- Git diffs show garbled characters
- Build automation breaks on some platforms

### Solution: Translate to English

Use `/ue-validate-asset-name` to detect and rename CJK assets.

**Translation Rules:**
1. **Translate literally** — Convert CJK characters to their English meaning
2. **No context guessing** — Don't add character/model names unless already in original name
3. **Keep structure** — Preserve underscores and segmentation

**Examples:**

| Original | ✅ CORRECT | ❌ WRONG |
|----------|------------|----------|
| `M_下擺` | `MI_Hem` | `MI_AliceSwimsuit_Hem` (added context) |
| `M_体_outline` | `MI_Body_Outline` | `MI_SomeCharacter_Body_Outline` (guessed) |
| `T_岩石_diffuse` | `T_Rock_D` | `T_MountainRock_D` (over-specified) |
| `SM_캐릭터` | `SM_Character` | `SM_MainCharacter` (guessed) |

### Known API Limitations

**Problem:** `EditorAssetLibrary.rename_asset()` fails on CJK paths.

**Workaround:**
1. Use `duplicate_loaded_asset()` to create copy with English name
2. Use `consolidate_assets()` to redirect all references from old → new
3. Delete old CJK asset

**DON'T** use `duplicate_asset()` + `delete_asset()` — breaks ALL references.

---

## Validation & Automation

### Manual Validation

Use `/ue-validate-asset-name` command to validate selected assets:

```bash
# In Claude Code:
/ue-validate-asset-name --export
```

This remotely executes validation script in UE Editor and shows results.

### Automated Validation

Integrate into your pipeline:

```python
# In UE Editor Python:
exec(open(r"skills/ue-validate-asset-name/validate_name.py").read())
```

Output: `.agent-local/private/unreal/name-validate/batch_YYYYMMDD_HHMMSS.json`

### Batch Rename

After reviewing validation results:

```bash
/ue-validate-asset-name --rename
```

Applies suggested names to all assets with violations.

---

## Exceptions

### Maps / Levels

Maps (World assets) traditionally **do not use prefixes**. Use descriptive names instead:

```
✅ GOOD:
MainMenu
Level_01_Forest
Level_02_Cave
TestMap

❌ BAD:
W_MainMenu             # Unnecessary prefix
MAP_Level01
```

### Legacy Assets

If working with legacy projects that don't follow these conventions:
- **New assets**: Follow this standard
- **Existing assets**: Rename during refactoring/cleanup sprints
- **High-risk renames**: Use `consolidate_assets()` to preserve references

---

## Quick Reference

### Common Prefixes

```
Meshes:      SM_, SK_
Materials:   M_, MI_, MF_
Textures:    T_, TC_, RT_
Blueprints:  BP_, WBP_
Animations:  AS_, AM_, ABP_, BS_
VFX:         FXS_, FXE_, PS_
Sounds:      A_
Physics:     PHYS_
Skeletons:   SKEL_
Data:        DT_, Curve_
AI:          BT_, BB_, EQS_
```

### Texture Suffixes

```
_D, _BC:     Diffuse/BaseColor
_N:          Normal
_R:          Roughness
_M, _MT:     Metallic
_AO, _O:     Ambient Occlusion
_E:          Emissive
_A:          Alpha/Opacity
_ORM:        Packed (Occlusion+Roughness+Metallic)
```

### Pattern

```
[Prefix]_[BaseName]_[OptionalDetails]_[Number]

SM_Rock_01
T_Rock_D
MI_Character_Skin_Blue
```

---

*Consistency is automation. Automation is scale.*
