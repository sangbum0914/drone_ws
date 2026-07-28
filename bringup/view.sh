#!/bin/bash
# 환경 소싱 + 실시간 카메라 뷰어 (기본 front_45)
source /home/sangbum/drone_ws/bringup/env.sh
exec python3 /home/sangbum/drone_ws/bringup/live_view.py "${1:-front_45}"
