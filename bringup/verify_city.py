import unreal
unreal.EditorLoadingAndSavingUtils.load_map("/Game/FlyingCPP/Maps/FlyingExampleMap")
acts = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
bldg = [a for a in acts if a.get_actor_label().startswith("Bldg_")]
sm = [a for a in acts if isinstance(a, unreal.StaticMeshActor)]
unreal.log(f"CITYCHECK buildings={len(bldg)} total_actors={len(acts)} staticmesh={len(sm)}")
