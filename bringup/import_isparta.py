"""실사 도시블록(Isparta, CC-BY) 을 맵에 통합. 캐니언/잔재 제거 후 배치."""
import unreal
GLB="/home/sangbum/drone_ws/external/city_assets/isparta/isparta.glb"
DEST="/Game/Isparta"; MAP="/Game/FlyingCPP/Maps/FlyingExampleMap"
TARGET=13000.0  # 최장 수평축 목표(cm)=130m 실스케일 유지

def main():
    t=unreal.AssetImportTask(); t.filename=GLB; t.destination_path=DEST
    t.automated=True; t.save=True; t.replace_existing=True
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
    meshes=[unreal.EditorAssetLibrary.load_asset(p) for p in unreal.EditorAssetLibrary.list_assets(DEST,recursive=True)]
    meshes=[m for m in meshes if isinstance(m,unreal.StaticMesh)]
    unreal.log(f"ISPARTA meshes={len(meshes)}")
    if not meshes: unreal.log_error("ISPARTA 메시 없음"); return
    lo=[1e18]*3; hi=[-1e18]*3
    for m in meshes:
        b=m.get_bounding_box()
        for i,ax in enumerate(('x','y','z')):
            lo[i]=min(lo[i],getattr(b.min,ax)); hi[i]=max(hi[i],getattr(b.max,ax))
    size=[hi[i]-lo[i] for i in range(3)]; ctr=[(hi[i]+lo[i])/2 for i in range(3)]
    scale=TARGET/max(size[0],size[1],1.0)
    unreal.log(f"ISPARTA size={size} scale={scale:.4f}")
    unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    sub=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    rm=0
    for a in sub.get_all_level_actors():
        lb=a.get_actor_label()
        if lb.startswith("Bldg_") or lb.startswith("Photoreal_") or lb.startswith("Isparta_"):
            sub.destroy_actor(a); rm+=1
    unreal.log(f"ISPARTA 잔재제거={rm}")
    for i,m in enumerate(meshes):
        loc=unreal.Vector(-ctr[0]*scale,-ctr[1]*scale,-lo[2]*scale)
        a=sub.spawn_actor_from_object(m,loc,unreal.Rotator(0,0,0))
        if a: a.set_actor_scale3d(unreal.Vector(scale,scale,scale)); a.set_actor_label(f"Isparta_{i}")
    unreal.log(f"ISPARTA 배치={len(meshes)}")
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
    unreal.log("ISPARTA 저장완료")
main()
