---
name: "ue-generate-spritesheet"
description: Generate UE flipbook sprite sheets.
domains: unreal
repo-keys: anju,mega-melange
languages: python
task-types: implementation
context-profile: unreal-engine
exclude-when: rust,web,obsidian
activation-check: normal
---

# ue-generate-spritesheet

## Step 0: Activation Check

- Continue only when the request explicitly matches `ue-generate-spritesheet` and its Unreal Engine responsibility.
- Confirm the target UE project, selected asset or input path, expected output, and whether the task may mutate assets.
- If target, scope, or destructive intent is unclear, ask before running scripts or editing files.
- Stop for non-Unreal, generic coding, or unrelated asset questions.
- Do not read skill-local references, run scripts, or follow later steps until this check passes.


Generate sprite sheets from image sequence folders for UE flipbook textures.

## Purpose

Batch-converts folders of image sequences (PNG/JPG/WebP) into sprite sheet textures suitable for UE flipbooks. Each subfolder in the input directory becomes one sprite sheet.

Features:
- Center-crop + LANCZOS resize to uniform frame size
- Configurable frame dimensions, FPS reduction, sheet size
- Optional `png/` subfolder convention
- Batch processing of multiple sequence folders

## Usage

```
/ue-generate-spritesheet <input_path> [options]
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--input` | (required) | Input directory containing sequence folders |
| `--output` | `.agent-local/private/unreal/spritesheet-generate/` | Output directory |
| `--frame_width` | 80 | Frame width in pixels |
| `--frame_height` | 80 | Frame height in pixels |
| `--fps_reduction` | 1 | Sample every Nth frame (2 = half FPS) |
| `--use_png_subfolder` | True | Look for images in `png/` subfolder |
| `--max_width` | 1024 | Max sprite sheet width |
| `--max_height` | 1024 | Max sprite sheet height |

### Examples

```bash
# Basic usage
python skills/ue-generate-spritesheet/generate_spritesheet.py --input ~/sequences/

# Custom frame size for facial animations (no png subfolder)
python skills/ue-generate-spritesheet/generate_spritesheet.py \
  --input ~/faces/ --frame_width 260 --frame_height 145 \
  --use_png_subfolder False --fps_reduction 2
```

### Input Structure

```
input/
├── animation_01/
│   └── png/           # if --use_png_subfolder True
│       ├── 0001.png
│       ├── 0002.png
│       └── ...
├── animation_02/
│   └── png/
│       ├── 0001.png
│       └── ...
```

## Output

Sprite sheets saved to: `.agent-local/private/unreal/spritesheet-generate/`

Filename pattern: `{folder_name}_{frame_count}.png`

## Files

- `generate_spritesheet.py` - Main script (PIL-based, no UE dependency)

## Related Files

- Skill: `skills/ue-generate-spritesheet/SKILL.md`
- Output: `.agent-local/private/unreal/spritesheet-generate/`
