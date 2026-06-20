---
name: "ue-validate-asset-name"
description: Validate and fix Unreal asset names.
activation-check: normal
domains: unreal
repo-keys: anju,mega-melange
languages: python
task-types: implementation
context-profile: unreal-engine
exclude-when: rust,web,obsidian
---

# ue-validate-asset-name

## Step 0: Activation Check

- Continue only when the request explicitly matches `ue-validate-asset-name` and its specific responsibility.
- Confirm target workspace, target files or artifact path, required input, and expected output.
- If target or scope is unclear, ask before editing files or running local mutating commands.
- If the request is generic or better handled by another skill, stop and route there.
- Do not read skill-local references, run scripts, or follow later steps until this check passes.

## Responsibility

"Validate and fix UE asset names against naming conventions. Use when checking Unreal Engine asset naming."

## After Activation

After Step 0 passes, read [flow.md](flow.md) and follow that workflow. Do not load this detail for generic or mismatched requests.
