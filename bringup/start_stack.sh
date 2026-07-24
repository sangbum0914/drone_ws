#!/bin/bash
# 드론 sim 스택 전체를 올바른 순서로 기동한다 (터미널에서 직접 실행 권장).
# 순서: AirSim(4560 리슨) → PX4 SITL(연결·lockstep) → MicroXRCEAgent → airsim_node
#
# 알려진 함정:
#  - PX4 pxh 콘솔이 escape 코드를 폭주시킴 → 출력은 /dev/null 로 폐기.
#  - /fmu 토픽 확인 시 px4_msgs(ros2_ws) 소싱 필수 (verify_stack.sh 사용).
#  - 반복 재기동 시 stale 프로세스 정리 후 진행.
# set -u 금지: ROS setup.bash 가 unbound 변수를 참조함
source /home/sangbum/drone_ws/bringup/env.sh
export DISPLAY="${DISPLAY:-:0}"
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/1000}"

echo "[0/4] 기존 프로세스 정리..."
for n in px4 MicroXRCEAgent UnrealEditor airsim_node; do
  p=$(pgrep -x "$n"); [ -n "$p" ] && kill -9 $p 2>/dev/null
done
sleep 3

echo "[1/4] AirSim Blocks 실행 (데스크톱 창)..."
setsid "$UE_ROOT/Engine/Binaries/Linux/UnrealEditor" "$BLOCKS_UPROJECT" \
    -game -windowed -ResX=1280 -ResY=720 > "$BRINGUP/airsim_blocks.log" 2>&1 &
echo "    4560 리슨 대기..."
for i in $(seq 1 90); do
  ss -ltn 2>/dev/null | grep -qE ':4560[[:space:]]' && break
  sleep 5
done
ss -ltn 2>/dev/null | grep -qE ':4560[[:space:]]' || { echo "    ERROR: AirSim 4560 안 열림"; exit 1; }
echo "    AirSim ready."

echo "[2/4] PX4 SITL 기동 (AirSim 연결)..."
( cd "$PX4_DIR" && setsid env PX4_SIM_HOSTNAME=localhost make px4_sitl none_iris \
    < /dev/null > /dev/null 2>&1 & )
sleep 20

echo "[3/4] MicroXRCEAgent 기동..."
setsid MicroXRCEAgent udp4 -p 8888 > "$BRINGUP/xrce_agent.log" 2>&1 &
sleep 2

echo "[4/4] airsim_node 기동..."
# enable_object_transforms_list:=False → object_transforms의 null-char FastDDS 크래시(및 odom_local 동반 정지) 회피
# publish_clock:=True → /clock 발행 (use_sim_time 사용 가능)
setsid ros2 launch airsim_ros_pkgs airsim_node.launch.py output:=screen \
    enable_object_transforms_list:=False publish_clock:=True \
    > "$BRINGUP/airsim_node.log" 2>&1 &
sleep 5

echo "[5/5] GT publisher 기동 (전용 RPC, airsim_node odom 루프 우회)..."
setsid python3 "$BRINGUP/gt_publisher.py" > "$BRINGUP/gt_publisher.log" 2>&1 &
sleep 3

echo "완료. 검증: bash $BRINGUP/verify_stack.sh"
