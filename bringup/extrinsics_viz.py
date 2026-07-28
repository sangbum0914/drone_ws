#!/usr/bin/env python3
"""쿼드로터 센서 extrinsics 3D 시각화 (settings.json 기준).

기체 body(FRD: X-전방 red, Y-우 green, Z-하 blue) + 각 카메라의 위치·광축을
3D로 그려 PNG 저장. AirSim FRD → ROS optical(RDF) 변환도 주석으로 표기.
"""
import json
import math
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SETTINGS = "/home/sangbum/drone_ws/sim/airsim/settings.json"
OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/extrinsics.png"


def look_dir(pitch_deg, roll_deg, yaw_deg):
    """AirSim Pitch/Roll/Yaw(deg, FRD) → 광축(전방) 단위벡터 (body FRD)."""
    p, r, y = map(math.radians, (pitch_deg, roll_deg, yaw_deg))
    # 기본 전방 +X, yaw(Z)·pitch(Y) 순 적용 (roll은 광축방향 불변)
    cx = math.cos(p) * math.cos(y)
    cy = math.cos(p) * math.sin(y)
    cz = -math.sin(p)  # pitch<0 → +Z(하향)
    return np.array([cx, cy, cz])


def main():
    cams = json.load(open(SETTINGS))["Vehicles"]["Drone1"]["Cameras"]
    fig = plt.figure(figsize=(12, 9))
    ax = fig.add_subplot(111, projection="3d")

    # --- 기체 body FRD 프레임 (원점) ---
    L = 0.5
    ax.quiver(0, 0, 0, L, 0, 0, color="r", lw=3, arrow_length_ratio=0.15)
    ax.quiver(0, 0, 0, 0, L, 0, color="g", lw=3, arrow_length_ratio=0.15)
    ax.quiver(0, 0, 0, 0, 0, L, color="b", lw=3, arrow_length_ratio=0.15)
    ax.text(L * 1.1, 0, 0, "X (Forward)", color="r", fontsize=10, weight="bold")
    ax.text(0, L * 1.1, 0, "Y (Right)", color="g", fontsize=10, weight="bold")
    ax.text(0, 0, L * 1.15, "Z (Down)", color="b", fontsize=10, weight="bold")

    # --- 쿼드로터 X-형 팔 (문맥용) ---
    a = 0.22
    for sx, sy in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
        ax.plot([0, sx * a], [0, sy * a], [0, 0], color="0.4", lw=2)
        ax.scatter(sx * a, sy * a, 0, color="0.3", s=120)  # 로터
    ax.scatter(0, 0, 0, color="k", s=60)
    ax.text(0.02, 0.02, -0.05, "IMU/body", fontsize=9)

    # --- 각 카메라: 위치 + 광축 ---
    colors = {"front_center": "#d95f02", "bottom_center": "#7570b3",
              "front_45": "#1b9e77"}
    for name, d in cams.items():
        pos = np.array([d.get("X", 0), d.get("Y", 0), d.get("Z", 0)])
        ld = look_dir(d.get("Pitch", 0), d.get("Roll", 0), d.get("Yaw", 0))
        c = colors.get(name, "m")
        ax.scatter(*pos, color=c, s=140, marker="s", edgecolors="k")
        ax.quiver(pos[0], pos[1], pos[2], ld[0] * 0.35, ld[1] * 0.35,
                  ld[2] * 0.35, color=c, lw=2.5, arrow_length_ratio=0.25)
        ax.text(pos[0] + ld[0] * 0.38, pos[1] + ld[1] * 0.38,
                pos[2] + ld[2] * 0.38,
                f"{name} (P={d.get('Pitch',0):.0f}deg)", color=c, fontsize=9)

    ax.set_xlabel("X forward (m)"); ax.set_ylabel("Y right (m)")
    ax.set_zlabel("Z down (m)")
    ax.set_title("Quadrotor Camera Extrinsics (AirSim body = FRD)\n"
                 "arrow = optical axis (look/+Z),  square = camera position",
                 fontsize=12)
    ax.set_xlim(-0.4, 0.7); ax.set_ylim(-0.5, 0.5); ax.set_zlim(0.4, -0.4)
    ax.view_init(elev=22, azim=-58)

    note = ("AirSim body: FRD (X-fwd, Y-right, Z-down)\n"
            "ROS base_link: FLU (X-fwd, Y-left, Z-up)  → R_body = diag(1,-1,-1)\n"
            "Camera optical (REP-103): x-right, y-down, z-forward(look)\n"
            "=> VIO must convert settings values FRD->FLU->optical to get T_base_camopt")
    fig.text(0.02, 0.02, note, fontsize=9, family="monospace",
             bbox=dict(boxstyle="round", fc="#f5f5f5", ec="0.6"))
    plt.tight_layout()
    plt.savefig(OUT, dpi=130, bbox_inches="tight")
    print(f"saved {OUT}")


main()
