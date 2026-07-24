#!/bin/bash
# AirSim Blocks 환경을 데스크톱 창으로 실행 (PX4 lockstep 시뮬레이터 역할).
# 첫 실행은 셰이더 컴파일로 수 분 소요. 로그는 $LOG 에 기록.
set -u

UE=/home/sangbum/drone_ws/external/UnrealEngine_5.8
BLOCKS=/home/sangbum/drone_ws/external/Cosys-AirSim/Unreal/Environments/Blocks/Blocks.uproject
LOG=/home/sangbum/drone_ws/bringup/airsim_blocks.log

# 데스크톱(Wayland/XWayland) 세션에 렌더
export DISPLAY="${DISPLAY:-:0}"
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/1000}"

echo "AirSim Blocks 실행 → 로그: $LOG"
"$UE/Engine/Binaries/Linux/UnrealEditor" "$BLOCKS" \
    -game -windowed -ResX=1280 -ResY=720 \
    > "$LOG" 2>&1
