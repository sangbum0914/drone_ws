#!/bin/bash
# 스택 상태 + 토픽 흐름 검증 (Phase 0 conformance 일부).
source /home/sangbum/drone_ws/bringup/env.sh

echo "=== 프로세스 ==="
for n in UnrealEditor px4 MicroXRCEAgent airsim_node; do
  printf "  %-16s %s\n" "$n" "$(pgrep -x $n >/dev/null && echo LIVE || echo DEAD)"
done

echo "=== 소켓 ==="
echo "  4560(PX4<->AirSim lockstep): $(ss -tn 2>/dev/null | grep -c ':4560') ESTAB"
echo "  8888(uXRCE agent)          : $(ss -un 2>/dev/null | grep -c ':8888') "

echo "=== PX4 DDS 토픽 (px4_msgs 소싱 필수) ==="
for t in /fmu/out/sensor_combined /fmu/out/vehicle_odometry /fmu/out/vehicle_attitude \
         /fmu/out/vehicle_local_position_v1 /fmu/out/vehicle_gps_position; do
  r=$(timeout 5 ros2 topic hz "$t" 2>&1 | grep -oE "average rate: [0-9.]+" | head -1)
  printf "  %-42s %s\n" "$t" "${r:-무응답}"
done

echo "=== AirSim 센서/GT ==="
for t in /airsim_node/Drone1/imu/Imu /airsim_node/Drone1/gps/Gps \
         /airsim_node/Drone1/front_center_Scene/image /airsim_node/Drone1/odom_local; do
  r=$(timeout 6 ros2 topic hz "$t" 2>&1 | grep -oE "average rate: [0-9.]+" | head -1)
  printf "  %-46s %s\n" "$t" "${r:-무응답}"
done
