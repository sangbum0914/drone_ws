import unreal
unreal.EditorLoadingAndSavingUtils.load_map("/Game/FlyingCPP/Maps/FlyingExampleMap")
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
acts = sub.get_all_level_actors()
bldg = [a for a in acts if a.get_actor_label().startswith("Bldg_")]
photo = [a for a in acts if a.get_actor_label().startswith("Photoreal_")]
sm = [a for a in acts if isinstance(a, unreal.StaticMeshActor)]
unreal.log(f"AUDIT total={len(acts)} bldg={len(bldg)} photoreal={len(photo)} staticmesh={len(sm)}")
# 재질 미할당(보라) 메시 조사: Bldg 메시의 머티리얼 슬롯 확인
missing=0; checked=0
for a in bldg[:5]:
    comp = a.static_mesh_component
    if comp:
        mats = comp.get_materials()
        checked+=1
        for m in mats:
            if m is None: missing+=1
        unreal.log(f"AUDIT bldg {a.get_actor_label()} mats={len(mats)} none={sum(1 for m in mats if m is None)} first={mats[0].get_name() if mats and mats[0] else None}")
unreal.log(f"AUDIT missing_mat_slots(sampled)={missing}")
