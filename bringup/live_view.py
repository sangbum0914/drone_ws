#!/usr/bin/env python3
"""실시간 카메라 뷰어 — AirSim 클라이언트로 직접 프레임을 받아 창에 표시.

airsim_node(무거운 스캔에서 크래시) 우회. 데스크톱에서 실행:
    source ~/drone_ws/bringup/env.sh
    python3 ~/drone_ws/bringup/live_view.py [camera]
키: 1=front_center 2=front_45 3=bottom_center  q=종료
"""
import sys
import numpy as np
import cv2
sys.path.insert(0, "/home/sangbum/drone_ws/external/Cosys-AirSim/PythonClient")
import cosysairsim as airsim

CAMS = ["front_center", "front_45", "bottom_center"]
cam = sys.argv[1] if len(sys.argv) > 1 else "front_45"

c = airsim.MultirotorClient(ip="127.0.0.1", port=41451, timeout_value=30)
c.confirmConnection()
print(f"live_view: connected. camera={cam}  (1/2/3 전환, q 종료)")
cv2.namedWindow("AirSim Live", cv2.WINDOW_NORMAL)
cv2.resizeWindow("AirSim Live", 960, 540)

while True:
    try:
        r = c.simGetImages([airsim.ImageRequest(cam, airsim.ImageType.Scene, False, False)])[0]
        if r.height > 0:
            img = np.frombuffer(r.image_data_uint8, dtype=np.uint8).reshape(r.height, r.width, 3)
            img = np.ascontiguousarray(img[:, :, ::-1])  # RGB→BGR + writable
            cv2.putText(img, cam, (12, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9,
                        (0, 255, 0), 2)
            cv2.imshow("AirSim Live", img)
    except Exception as e:
        print("RPC:", e)
    k = cv2.waitKey(30) & 0xFF
    if k == ord("q"):
        break
    elif k in (ord("1"), ord("2"), ord("3")):
        cam = CAMS[k - ord("1")]
        print("camera ->", cam)
cv2.destroyAllWindows()
