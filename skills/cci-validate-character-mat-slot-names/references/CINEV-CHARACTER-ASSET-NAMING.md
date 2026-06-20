---
status: accepted
---
# CINEV Character Asset Naming Convention

Character asset naming rules for textures, materials, meshes, and blueprints.

---

## Format

```
[Prefix]_[Gender]_[CharacterName]_[DesignVer]_[PartCode]_[ColorCode]
```

- **ColorCode** is appended only to textures and materials.
- Meshes and FBX files omit Prefix and ColorCode.

### Example

```
T_F_Verte_V01_Hair_001_BkA
```

---

## Fields

| Field | Example | Description |
|-------|---------|-------------|
| **Prefix** | `T`, `MI`, `SK`, `BP` | Asset type identifier |
| **Gender** | `F`, `M`, `N` | Female / Male / Neutral |
| **CharacterName** | `Verte`, `Roy`, `Iris` | Unique character name |
| **DesignVer** | `V01`, `V02` | Design/modeling version (incremented on renewal) |
| **PartCode** | `Hair_001`, `Face`, `Body` | Model part identifier |
| **ColorCode** | `BkA`, `BnB`, `PkA` | Color family + tone level |

### Prefix List

| Prefix | Asset Type |
|--------|-----------|
| `T` | Texture |
| `MI` | Material Instance |
| `SK` | Skeletal Mesh |
| `BP` | Blueprint |

### Gender Code

| Code | Meaning |
|------|---------|
| `F` | Female |
| `M` | Male |
| `N` | Neutral |

### PartCode Numbering Rule

- Independent parts with multiple variations: append number (`Hair_001`, `Hair_002`)
- Sub-parts of head (Face, Eyes, Eyelash): no number suffix

---

## Color Code

Structure: **first letter + last letter of color name + tone level (A/B/C)**

Tone levels: A = darkest/base, B = mid, C = lightest

| Color | Code | Tones | Description |
|-------|------|-------|-------------|
| Black | `Bk` | `BkA`, `BkB`, `BkC` | Base black hair |
| Brown | `Bn` | `BnA`, `BnB` | Natural warm tones |
| Blond | `Bd` | `BdA`, `BdB` | Gold/blond hair |
| Pink | `Pk` | `PkA`, `PkB`, `PkC` | Character accent |
| Blue | `Be` | `BeA`, `BeB`, `BeC` | Cool tone hair |
| Silver | `Sr` | `SrA`, `SrB` | Gray/white hair |
| Red | `Rd` | `RdA`, `RdB` | Strong accent |
| Green | `Gn` | `GnA`, `GnB` | Point color |
| Purple | `Pe` | `PeA`, `PeB` | Fantasy/mystery |
| Orange | `Oe` | `OeA`, `OeB` | Warm accent |

---

## Examples

| Asset Type | Filename | Meaning |
|-----------|----------|---------|
| Texture | `T_F_Verte_V01_Hair_001_BkA` | Verte female, design v1, hair 001, Black-A tone |
| Material Instance | `MI_F_Verte_V01_Hair_001_BkA` | Same character's material instance |
| Eyes Texture | `T_M_Azul_V01_Eyes_BkA` | Azul male, eyes (no number, head sub-part) |
| Mesh/FBX | `F_Verte_V01_Hair_001` | Base mesh (no prefix, no color code) |

---

## Search Pattern

All assets for a character can be found with: `*_Verte_*`
