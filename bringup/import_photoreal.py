"""Sketchfab glb(실사 거리) 를 Blocks 맵에 통합 (Kenney 건물 제거 후 배치).

실행:
  UnrealEditor-Cmd <Blocks.uproject> -ExecutePythonScript=import_photoreal.py \
      -unattended -nosplash -nullrhi -stdout
로그는 Saved/Logs/Blocks.log 의 'PHOTOREAL' 태그로 확인.
"""
import unreal

GLB = "/home/sangbum/drone_ws/external/city_assets/photoreal/frozen_street.glb"
DEST = "/Game/Photoreal"
MAP = "/Game/FlyingCPP/Maps/FlyingExampleMap"
TARGET_LEN = 8000.0  # 씬 최장축 목표 길이 cm (80 m)


def import_glb():
    task = unreal.AssetImportTask()
    task.filename = GLB
    task.destination_path = DEST
    task.automated = True
    task.save = True
    task.replace_existing = True
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    # DEST 아래 생성된 StaticMesh 수집
    meshes = []
    for p in unreal.EditorAssetLibrary.list_assets(DEST, recursive=True):
        a = unreal.EditorAssetLibrary.load_asset(p)
        if isinstance(a, unreal.StaticMesh):
            meshes.append(a)
    return meshes


def combined_bounds(meshes):
    lo = [1e18, 1e18, 1e18]
    hi = [-1e18, -1e18, -1e18]
    for m in meshes:
        b = m.get_bounding_box()
        for i, ax in enumerate(("x", "y", "z")):
            lo[i] = min(lo[i], getattr(b.min, ax))
            hi[i] = max(hi[i], getattr(b.max, ax))
    return lo, hi


def main():
    unreal.log("PHOTOREAL: glb import 시작")
    meshes = import_glb()
    unreal.log(f"PHOTOREAL: import된 StaticMesh {len(meshes)}개")
    if not meshes:
        unreal.log_error("PHOTOREAL: 메시 없음 — 중단")
        return
    lo, hi = combined_bounds(meshes)
    size = [hi[i] - lo[i] for i in range(3)]
    ctr = [(hi[i] + lo[i]) / 2 for i in range(3)]
    unreal.log(f"PHOTOREAL: bounds size={size} center={ctr}")
    longest = max(size[0], size[1], 1.0)
    scale = TARGET_LEN / longest
    unreal.log(f"PHOTOREAL: scale={scale:.4f}")

    unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    # 기존 Kenney 건물 제거 (깔끔한 실사 씬)
    removed = 0
    for a in actor_sub.get_all_level_actors():
        if a.get_actor_label().startswith("Bldg_"):
            actor_sub.destroy_actor(a)
            removed += 1
    unreal.log(f"PHOTOREAL: Kenney 건물 {removed}개 제거")

    # 씬 배치: 중심을 원점으로, 바닥(z min)을 z=0 에 (드론은 원점 위 스폰)
    for i, m in enumerate(meshes):
        loc = unreal.Vector(
            -ctr[0] * scale, -ctr[1] * scale, -lo[2] * scale
        )
        actor = actor_sub.spawn_actor_from_object(m, loc, unreal.Rotator(0, 0, 0))
        if actor:
            actor.set_actor_scale3d(unreal.Vector(scale, scale, scale))
            actor.set_actor_label(f"Photoreal_{i}")
    unreal.log(f"PHOTOREAL: 배치 완료 {len(meshes)}개")
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    unreal.log("PHOTOREAL: 맵 저장 완료")


main()
