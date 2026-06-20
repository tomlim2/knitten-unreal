---
name: "cci-deploy-pmx-character"
description: Deploy PMX characters to UE.
argument-hint: "<pmx_path> --name <name> [--preset PRESET] [--no-spring] [--no-rename] [--scale N] [--gender Male|Female] [--no-build] [--no-open]"
allowed-tools:
  - Read
  - Glob
  - Bash(python:*)
  - Bash(cd:*)
  - Bash(start:*)
activation-check: normal
---

# cci-deploy-pmx-character

## Step 0: Activation Check

- Continue only when the request explicitly matches `cci-deploy-pmx-character` and its Unreal Engine responsibility.
- Confirm the target UE project, selected asset or input path, expected output, and whether the task may mutate assets.
- If target, scope, or destructive intent is unclear, ask before running scripts or editing files.
- Stop for non-Unreal, generic coding, or unrelated asset questions.
- Do not read skill-local references, run scripts, or follow later steps until this check passes.


Full pipeline: PMX → VRM conversion → UE character registration → open CINEV project.

## Arguments

```
$ARGUMENTS
```

Parse the arguments:
- First non-flag argument: input path (PMX file, ZIP, or directory)
- `--name <name>`: output VRM filename (**required** — used as character name)
- `--preset <name>`: spring bone preset (default: `default`)
- `--no-spring`: skip spring bone conversion
- `--no-rename`: skip ASCII rename step
- `--no-validate`: skip VRM validation step
- `--scale <number>`: scale factor (default: 0.08)
- `--gender Male|Female`: character gender (default: Female)
- `--no-build`: skip UE build step
- `--no-open`: skip opening the project after registration

If no arguments or no `--name` provided, show usage and stop.

## Paths

Read `.agent-local/private/agent-hub-config/repo-paths.json` to resolve:
- `anju` → converter root (`<path>/module/pmx2vrm`) and register script (`<path>/python/user_character_manager/register_vrm.py`)
- `cinev-engine` → UE engine root
- `cinev-studio` → UE project root

## Execution

### Step 1: Convert PMX → VRM

```bash
cd "<anju>/module/pmx2vrm" && python -m python.intake "<input>" --name <name> [--preset <preset>] [other flags]
```

Capture the output VRM path from the `-> <path>` line.

### Step 2: Register VRM in UE

```bash
cd "<anju>/python/user_character_manager" && python register_vrm.py "<vrm_path>" [--gender <gender>] [--no-build]
```

### Step 3: Open project (unless `--no-open`)

```bash
start "" "<cinev-engine>/Engine/Binaries/Win64/UnrealEditor.exe" "<cinev-studio>/CINEVStudio/CINEVStudio.uproject"
```

## Output

Report each step's result:
1. Converted: `<name>.vrm` at `<path>`
2. Registered: `<name>.character` in UserCharacter/
3. Editor launching (or skipped if `--no-open`)

If any step fails, stop and report the error.
