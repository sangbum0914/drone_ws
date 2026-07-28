"""기존 Blocks 큐브(1M_Cube_Chamfer)를 어반 캐니언으로 재배치.

- photoreal/Cone/Sphere 잔재 제거
- 큐브를 격자형 건물(높이 다양)로 재배치, 중앙 십자 거리 확보(드론 스폰)
- 재질 통일(보라/기본 → 일관 머티리얼)
드론은 원점 스폰 → 중앙 거리에서 이륙, 캐니언 사이 비행 가능.
"""
import unreal

MAP = "/Game/FlyingCPP/Maps/FlyingExampleMap"
GRID = 7            # GRID x GRID 건물 격자
CELL = 2200.0       # cm, 셀 간격(22m): 건물 footprint ~10m + 거리 ~12m
CLEAR = 1           # 중앙 CLEAR 반경(셀)은 거리로 비움
FOOT = 10.0         # 건물 footprint 스케일(=10m, 큐브 1m 기준)


def main():
    unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    acts = sub.get_all_level_actors()

    cubes, floor, mat = [], None, None
    for a in acts:
        if not isinstance(a, unreal.StaticMeshActor):
            continue
        comp = a.static_mesh_component
        sm = comp.get_editor_property("static_mesh") if comp else None
        nm = sm.get_name() if sm else ""
        if nm == "1M_Cube_Chamfer":
            cubes.append(a)
            if mat is None and comp.get_materials():
                mat = comp.get_materials()[0]  # 정상 큐브 재질 재사용
        elif nm == "TemplateFloor":
            floor = a
        else:
            # photoreal(Object_/Photoreal_), Cone, Sphere, Cylinder 등 잔재 제거
            if not a.get_actor_label().startswith("Player"):
                sub.destroy_actor(a)
    unreal.log(f"CANYON cubes={len(cubes)} floor={'Y' if floor else 'N'} mat={mat.get_name() if mat else None}")

    half = (GRID - 1) / 2.0
    used = 0
    for gx in range(GRID):
        for gy in range(GRID):
            if abs(gx - half) <= CLEAR and abs(gy - half) <= CLEAR:
                continue  # 중앙 거리
            if used >= len(cubes):
                break
            a = cubes[used]; used += 1
            h = 15.0 + ((gx * 7 + gy * 13) % 5) * 6.0  # 15~39m 높이 다양
            x = (gx - half) * CELL
            y = (gy - half) * CELL
            a.set_actor_location(unreal.Vector(x, y, h * 100 / 2), False, False)
            a.set_actor_scale3d(unreal.Vector(FOOT, FOOT, h))
            a.set_actor_label(f"Bldg_{gx}_{gy}")
            comp = a.static_mesh_component
            if mat:
                for i in range(len(comp.get_materials())):
                    comp.set_material(i, mat)
    # 남는 큐브는 멀리 치워 시야에서 제거
    for a in cubes[used:]:
        a.set_actor_location(unreal.Vector(0, 0, -100000), False, False)
    unreal.log(f"CANYON placed={used} buildings")
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    unreal.log("CANYON 저장 완료")


main()
