"""UE 헤드리스 스크립트: Kenney 건물 FBX 를 Blocks 맵에 격자 배치.

실행:
  UnrealEditor-Cmd <Blocks.uproject> -run=pythonscript -script=import_city.py \
      -unattended -nosplash -nullrhi
드론은 원점 스폰 → 중앙 ±CLEAR 영역은 비우고 주변에 건물 배치.
"""
import os
import math
import unreal

FBX_DIR = "/home/sangbum/drone_ws/external/city_assets/commercial/Models/FBX format"
DEST = "/Game/City"
MAP = "/Game/FlyingCPP/Maps/FlyingExampleMap"

GRID = 8            # GRID x GRID 셀
SPACING = 3000.0    # cm (30 m) 셀 간격
CLEAR = 1           # 중앙 CLEAR 셀 반경은 비움(드론 스폰)
TARGET_H = 2500.0   # 건물 목표 높이 cm (25 m)

# 저디테일 건물만 선별 (가벼움)
BUILDINGS = [
    "low-detail-building-a", "low-detail-building-b", "low-detail-building-c",
    "low-detail-building-d", "low-detail-building-e", "low-detail-building-f",
    "low-detail-building-h", "low-detail-building-j", "building-b", "building-f",
]


def import_building(name):
    """FBX 한 개를 static mesh 로 import, 에셋 경로 반환."""
    path = os.path.join(FBX_DIR, name + ".fbx")
    if not os.path.exists(path):
        unreal.log_warning(f"없음: {path}")
        return None
    task = unreal.AssetImportTask()
    task.filename = path
    task.destination_path = DEST + "/Meshes"
    task.destination_name = name
    task.automated = True
    task.save = True
    task.replace_existing = True
    ui = unreal.FbxImportUI()
    ui.import_mesh = True
    ui.import_as_skeletal = False
    ui.import_materials = True
    ui.import_textures = True
    sm = ui.static_mesh_import_data
    sm.set_editor_property("combine_meshes", True)
    sm.set_editor_property("generate_lightmap_u_vs", True)
    sm.set_editor_property("auto_generate_collision", True)
    task.options = ui
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    asset_path = f"{DEST}/Meshes/{name}"
    if unreal.EditorAssetLibrary.does_asset_exist(asset_path):
        return asset_path
    return None


def mesh_height(mesh):
    """static mesh 의 Z 크기(cm) 반환."""
    b = mesh.get_bounding_box()  # unreal.Box
    return max(1.0, b.max.z - b.min.z)


def main():
    unreal.log("=== 건물 import 시작 ===")
    meshes = []
    for name in BUILDINGS:
        ap = import_building(name)
        if ap:
            m = unreal.EditorAssetLibrary.load_asset(ap)
            if m:
                meshes.append(m)
                unreal.log(f"import OK: {name} (h={mesh_height(m):.0f}cm)")
    if not meshes:
        unreal.log_error("import된 건물 없음 — 중단")
        return

    unreal.log(f"=== 맵 로드: {MAP} ===")
    unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    half = (GRID - 1) / 2.0
    n = 0
    for gx in range(GRID):
        for gy in range(GRID):
            # 중앙 비움(드론 스폰)
            if abs(gx - half) <= CLEAR and abs(gy - half) <= CLEAR:
                continue
            mesh = meshes[(gx * GRID + gy) % len(meshes)]
            x = (gx - half) * SPACING
            y = (gy - half) * SPACING
            loc = unreal.Vector(x, y, 0.0)
            yaw = float(((gx * 37 + gy * 91) % 4) * 90)  # 유사난수 회전
            rot = unreal.Rotator(0.0, 0.0, yaw)
            actor = actor_sub.spawn_actor_from_object(mesh, loc, rot)
            if actor:
                # 목표 높이로 스케일
                h = mesh_height(mesh)
                s = TARGET_H / h * (0.7 + 0.6 * (((gx + gy) % 3) / 2.0))  # 높이 다양화
                actor.set_actor_scale3d(unreal.Vector(s, s, s))
                actor.set_actor_label(f"Bldg_{gx}_{gy}")
                n += 1
    unreal.log(f"=== 배치 완료: {n}동 ===")
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    unreal.log("=== 맵 저장 완료 ===")


main()
