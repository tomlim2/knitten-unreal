"""
Validate and rename selected UE assets based on naming conventions.

Run inside UE Editor Python console:
    exec(open(__import__("os").path.expanduser(r"~\\.agent-local\\skills\\ue-validate-asset-name\\validate_name.py")).read())

Supported: All asset types selectable in Content Browser.
Output: .agent-local/private/unreal/name-validate/{name}.json

Does NOT auto-rename. Exports validation results to JSON.
Renaming is triggered separately via --rename mode.
"""

import unreal
import json
import os
import re
from datetime import datetime


# ---------------------------------------------------------------------------
# Prefix table — Epic Official + Allar community standard (SM_ convention)
# ---------------------------------------------------------------------------

# Maps UE class name -> expected prefix
PREFIX_TABLE = {
    # Meshes
    "StaticMesh": "SM_",
    "SkeletalMesh": "SK_",
    # Animations
    "AnimSequence": "AS_",
    "AnimMontage": "AM_",
    "AnimBlueprint": "ABP_",
    "BlendSpace": "BS_",
    "BlendSpace1D": "BS_",
    "AimOffsetBlendSpace": "AO_",
    "AimOffsetBlendSpace1D": "AO_",
    # Materials
    "Material": "M_",
    "MaterialInstanceConstant": "MI_",
    "MaterialFunction": "MF_",
    "MaterialParameterCollection": "MPC_",
    "SubsurfaceProfile": "SSP_",
    "PhysicalMaterial": "PM_",
    # Textures
    "Texture2D": "T_",
    "TextureCube": "TC_",
    "TextureRenderTarget2D": "RT_",
    "MediaTexture": "MT_",
    # Blueprints
    "Blueprint": "BP_",
    "WidgetBlueprint": "WBP_",
    # Particles / Niagara
    "NiagaraSystem": "FXS_",
    "NiagaraEmitter": "FXE_",
    "NiagaraParameterCollection": "FXC_",
    "ParticleSystem": "PS_",
    # Sounds
    "SoundWave": "A_",
    "SoundCue": "A_",
    # Physics
    "PhysicsAsset": "PHYS_",
    # Skeletons
    "Skeleton": "SKEL_",
    # Data
    "DataTable": "DT_",
    "CurveFloat": "Curve_",
    "CurveVector": "Curve_",
    "CurveLinearColor": "Curve_",
    # AI
    "BehaviorTree": "BT_",
    "BlackboardData": "BB_",
    "EnvironmentQuery": "EQS_",
    # UI
    "Font": "Font_",
    "SlateBrushAsset": "Brush_",
    "SlateWidgetStyleAsset": "Style_",
    # Maps
    "World": "",
    "MapBuildDataRegistry": "",
}

# Texture suffix table — known channel suffixes
TEXTURE_SUFFIXES = {
    "_D": "Diffuse/BaseColor",
    "_BC": "BaseColor",
    "_N": "Normal",
    "_R": "Roughness",
    "_M": "Metallic",
    "_MT": "Metallic",
    "_S": "Specular",
    "_AO": "AmbientOcclusion",
    "_O": "Occlusion",
    "_E": "Emissive",
    "_A": "Alpha/Opacity",
    "_H": "Height",
    "_B": "Bump",
    "_DP": "Displacement",
    "_FM": "FlowMap",
    "_L": "LightMap",
    "_ORM": "Packed(O+R+M)",
    "_ORA": "Packed(O+R+A)",
    "_MRA": "Packed(M+R+A)",
    "_MRO": "Packed(M+R+O)",
}

# Sound Cue suffix
SOUND_CUE_SUFFIX = "_Cue"


# ---------------------------------------------------------------------------
# Validation rules
# ---------------------------------------------------------------------------

def validate_asset(asset):
    """Run all naming rules on a single asset. Returns dict with issues."""
    name = asset.get_name()
    path = asset.get_path_name()
    class_name = asset.get_class().get_name()

    issues = []
    suggested_name = name

    # --- Rule 1: English-only (no non-ASCII) ---
    has_non_ascii = not name.isascii()
    if has_non_ascii:
        issues.append({
            "rule": "ASCII_ONLY",
            "severity": "ERROR",
            "detail": "Asset name contains non-ASCII characters",
        })

    # --- Rule 2: Allowed characters [A-Za-z0-9_] ---
    if not re.match(r'^[A-Za-z0-9_]+$', name):
        bad_chars = set(re.findall(r'[^A-Za-z0-9_]', name))
        issues.append({
            "rule": "ALLOWED_CHARS",
            "severity": "ERROR",
            "detail": f"Forbidden characters: {bad_chars}",
        })
        # Strip forbidden chars from suggestion (only useful for ASCII names).
        # CJK names need manual translation — suggested_name is set to None later.
        suggested_name = re.sub(r'[^A-Za-z0-9_]', '', suggested_name)

    # --- Rule 3: No consecutive underscores ---
    if '__' in name:
        issues.append({
            "rule": "NO_DOUBLE_UNDERSCORE",
            "severity": "WARN",
            "detail": "Contains consecutive underscores '__'",
        })
        suggested_name = re.sub(r'_+', '_', suggested_name)

    # --- Rule 4: No trailing underscore ---
    if name.endswith('_'):
        issues.append({
            "rule": "NO_TRAILING_UNDERSCORE",
            "severity": "WARN",
            "detail": "Name ends with '_'",
        })
        suggested_name = suggested_name.rstrip('_')

    # --- Rule 5: Correct prefix ---
    expected_prefix = PREFIX_TABLE.get(class_name)
    if expected_prefix is not None and expected_prefix != "":
        if not name.startswith(expected_prefix):
            # Check if it has a WRONG prefix from another type
            has_wrong_prefix = False
            for other_prefix in sorted(set(PREFIX_TABLE.values()), key=len, reverse=True):
                if other_prefix and name.startswith(other_prefix) and other_prefix != expected_prefix:
                    has_wrong_prefix = True
                    break

            issues.append({
                "rule": "PREFIX",
                "severity": "ERROR",
                "detail": f"Expected prefix '{expected_prefix}' for {class_name}, "
                          f"{'has wrong prefix' if has_wrong_prefix else 'missing prefix'}",
            })

            # Suggest fix: strip wrong prefix if present, add correct one
            base = suggested_name
            if has_wrong_prefix:
                for other_prefix in sorted(set(PREFIX_TABLE.values()), key=len, reverse=True):
                    if other_prefix and base.startswith(other_prefix):
                        base = base[len(other_prefix):]
                        break
            suggested_name = expected_prefix + base

    # --- Rule 6: PascalCase base name ---
    # Extract base name (after prefix, before variant number suffix)
    base_name = name
    if expected_prefix and name.startswith(expected_prefix):
        base_name = name[len(expected_prefix):]

    # Split by underscore, check each segment starts with uppercase
    segments = base_name.split('_')
    for seg in segments:
        if seg and seg[0].islower():
            issues.append({
                "rule": "PASCAL_CASE",
                "severity": "WARN",
                "detail": f"Segment '{seg}' should start with uppercase (PascalCase)",
            })
            break  # Report once

    # --- Rule 7: Zero-padded variant numbers ---
    # Check trailing numeric segments like _1, _001 (should be _01, _02)
    num_match = re.search(r'_(\d+)$', name)
    if num_match:
        num_str = num_match.group(1)
        if len(num_str) == 1:
            issues.append({
                "rule": "ZERO_PADDED_NUMBER",
                "severity": "WARN",
                "detail": f"Variant number '_{num_str}' should be zero-padded: '_{num_str.zfill(2)}'",
            })
            suggested_name = re.sub(r'_(\d)$', lambda m: f'_{m.group(1).zfill(2)}', suggested_name)
        elif len(num_str) >= 3 and int(num_str) < 100:
            issues.append({
                "rule": "ZERO_PADDED_NUMBER",
                "severity": "WARN",
                "detail": f"Variant '_{num_str}' over-padded for <100 variants, prefer 2-digit: '_{int(num_str):02d}'",
            })

    # --- Rule 8: Texture suffix check ---
    if class_name == "Texture2D":
        has_known_suffix = False
        for suffix in sorted(TEXTURE_SUFFIXES.keys(), key=len, reverse=True):
            # Check if name ends with suffix (before any variant number)
            name_without_number = re.sub(r'_\d+$', '', name)
            if name_without_number.endswith(suffix):
                has_known_suffix = True
                break
        if not has_known_suffix:
            issues.append({
                "rule": "TEXTURE_SUFFIX",
                "severity": "WARN",
                "detail": "Texture has no recognized channel suffix (_D, _N, _R, _M, _AO, etc.)",
            })

    # --- Rule 9: Sound Cue suffix ---
    if class_name == "SoundCue" and not name.endswith(SOUND_CUE_SUFFIX):
        issues.append({
            "rule": "SOUND_CUE_SUFFIX",
            "severity": "WARN",
            "detail": f"SoundCue should end with '{SOUND_CUE_SUFFIX}'",
        })
        suggested_name = suggested_name + SOUND_CUE_SUFFIX

    # CJK names produce garbage suggestions (stripped to empty/partial names).
    # Set to None so rename_assets.py skips them — Claude provides translations.
    if has_non_ascii:
        suggested_name = None

    result = {
        "name": name,
        "path": path,
        "class": class_name,
        "exported_at": datetime.now().isoformat(timespec="seconds"),
        "issues": issues,
        "suggested_name": suggested_name if suggested_name != name else None,
        "status": "PASS" if not issues else ("ERROR" if any(i["severity"] == "ERROR" for i in issues) else "WARN"),
    }

    return result


# ---------------------------------------------------------------------------
# Save helpers
# ---------------------------------------------------------------------------

def save_json(data, filename):
    """Save validation result to output directory."""
    output_dir = os.path.join(
        __import__("os").path.expanduser("~"), ".agent-local", "private", "unreal", "name-validate"
    )
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{filename}.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    unreal.log(f"[NameValidate] Saved: {output_path}")
    return output_path


# ---------------------------------------------------------------------------
# Main — validate mode (default)
# ---------------------------------------------------------------------------

def main():
    selected = unreal.EditorUtilityLibrary.get_selected_assets()

    if not selected:
        unreal.log_error("[NameValidate] No assets selected. Select assets in the Content Browser.")
        return

    results = []
    error_count = 0
    warn_count = 0
    pass_count = 0

    for asset in selected:
        result = validate_asset(asset)
        results.append(result)

        if result["status"] == "ERROR":
            error_count += 1
        elif result["status"] == "WARN":
            warn_count += 1
        else:
            pass_count += 1

        # Log per-asset summary
        if result["issues"]:
            severity_icon = "ERROR" if result["status"] == "ERROR" else "WARN"
            unreal.log_warning(
                f"[NameValidate] {severity_icon}: '{result['name']}' ({result['class']}) — "
                f"{len(result['issues'])} issue(s)"
            )
            for issue in result["issues"]:
                unreal.log_warning(f"  [{issue['severity']}] {issue['rule']}: {issue['detail']}")
            if result["suggested_name"]:
                unreal.log(f"  -> Suggested: '{result['suggested_name']}'")
        else:
            unreal.log(f"[NameValidate] PASS: '{result['name']}' ({result['class']})")

    # Save batch result
    batch = {
        "validated_at": datetime.now().isoformat(timespec="seconds"),
        "summary": {
            "total": len(results),
            "error": error_count,
            "warn": warn_count,
            "pass": pass_count,
        },
        "assets": results,
    }
    save_json(batch, f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

    unreal.log(
        f"[NameValidate] Done. {len(results)} asset(s): "
        f"{pass_count} pass, {warn_count} warn, {error_count} error"
    )


main()
