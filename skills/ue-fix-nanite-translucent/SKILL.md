---
description: Fix Nanite translucent material ordering.
domains: unreal
repo-keys: anju,mega-melange
languages: python
task-types: implementation
context-profile: unreal-engine
exclude-when: rust,web,obsidian
name: ue-fix-nanite-translucent
activation-check: normal
---

# ue-fix-nanite-translucent v0.1.0

## Step 0: Activation Check

- Continue only when the request explicitly matches `ue-fix-nanite-translucent` and its Unreal Engine responsibility.
- Confirm the target UE project, selected asset or input path, expected output, and whether the task may mutate assets.
- If target, scope, or destructive intent is unclear, ask before running scripts or editing files.
- Stop for non-Unreal, generic coding, or unrelated asset questions.
- Do not read skill-local references, run scripts, or follow later steps until this check passes.


## Changelog
- 0.1.0: Initial version

## Purpose

선택한 마테리얼이 Translucent일 때, 해당 마테리얼을 참조하는 Static Mesh를 찾아 Nanite가 켜져 있으면 끕니다.
Translucent + Nanite 조합은 UE에서 렌더링 문제를 일으키므로 자동으로 잡아줍니다.

## Usage

### One-step (recommended)
Content Browser에서 마테리얼 선택 후:
```
/ue-fix-nanite-translucent
```

### Manual two-step
1. UE Editor에서 직접 실행:
   ```
   python run_in_editor.py fix_nanite_translucent.py
   ```
2. 로그 출력에서 결과 확인

## Flow

1. 선택된 에셋 중 Material / MaterialInstanceConstant 필터링
2. Blend Mode가 Translucent인 것만 추출
3. AssetRegistry로 각 마테리얼의 Referencer 조회
4. StaticMesh만 필터링
5. Nanite 켜져 있으면 끄고 저장

## Related Files

- `fix_nanite_translucent.py` — UE Editor 내부 실행 스크립트
- `run_in_editor.py` — 리모트 실행 전송기
