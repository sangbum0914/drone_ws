"""AirSim 클라이언트로 직접 simGetImages 한 방 캡처 (airsim_node 우회, 안정)."""
import sys, numpy as np
sys.path.insert(0,"/home/sangbum/drone_ws/external/Cosys-AirSim/PythonClient")
import cosysairsim as airsim
from PIL import Image
out=sys.argv[1]; cam=sys.argv[2] if len(sys.argv)>2 else "front_45"
c=airsim.MultirotorClient(ip="127.0.0.1",port=41451,timeout_value=30)
c.confirmConnection()
r=c.simGetImages([airsim.ImageRequest(cam, airsim.ImageType.Scene, False, False)])[0]
img=np.frombuffer(r.image_data_uint8,dtype=np.uint8).reshape(r.height,r.width,3)
Image.fromarray(img[:,:,::-1] if False else img,"RGB").save(out)
print(f"DIRECT saved {out} {img.shape} cam={cam}")
