import unreal
unreal.EditorLoadingAndSavingUtils.load_map("/Game/FlyingCPP/Maps/FlyingExampleMap")
acts = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
bldg=[a for a in acts if a.get_actor_label().startswith("Bldg_")]
photo=[a for a in acts if a.get_actor_label().startswith("Photoreal_")]
unreal.log(f"DIAG bldg={len(bldg)} photoreal={len(photo)}")
for a in photo[:3]:
    l=a.get_actor_location(); s=a.get_actor_scale3d()
    unreal.log(f"DIAG photo loc=({l.x:.0f},{l.y:.0f},{l.z:.0f}) scale=({s.x:.3f})")
