#!/bin/bash
# 환경 소싱 + 키보드 teleop (한 방)
source /home/sangbum/drone_ws/bringup/env.sh
exec python3 /home/sangbum/drone_ws/bringup/keyboard_teleop.py "$@"
