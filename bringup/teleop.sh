#!/bin/bash
# 환경 소싱 + 잔여 offboard 컨트롤러 정리 + 키보드 teleop
source /home/sangbum/drone_ws/bringup/env.sh
# 충돌 방지: 기존 teleop/스크립트 비행 종료 (이 스크립트 cmdline엔 py 이름 없어 안전)
pkill -9 -f keyboard_teleop.py 2>/dev/null
pkill -9 -f fly_demo.py 2>/dev/null
pkill -9 -f climb_hold.py 2>/dev/null
sleep 1
echo ">>> 키보드 teleop 시작. T=이륙, WASD/RF/QE=조종, L=착륙, Ctrl-C=종료"
exec python3 /home/sangbum/drone_ws/bringup/keyboard_teleop.py "$@"
