#!/bin/bash
# 드론 sim 스택 공통 환경 소싱.
# ⚠️ 중요: /fmu (PX4 DDS) 토픽을 보려면 px4_msgs(ros2_ws)를 반드시 소싱해야 한다.
#   소싱 안 하면 ROS2 CLI가 메시지를 역직렬화 못 해 "무응답"으로 보인다(데이터는 정상).
source /opt/ros/jazzy/setup.bash
source /home/sangbum/drone_ws/external/Cosys-AirSim/ros2/install/setup.bash 2>/dev/null
source /home/sangbum/drone_ws/ros2_ws/install/setup.bash 2>/dev/null

# 경로
export UE_ROOT=/home/sangbum/drone_ws/external/UnrealEngine_5.8
export PX4_DIR=/home/sangbum/drone_ws/external/PX4-Autopilot
export AIRSIM_DIR=/home/sangbum/drone_ws/external/Cosys-AirSim
export BLOCKS_UPROJECT="$AIRSIM_DIR/Unreal/Environments/Blocks/Blocks.uproject"
export BRINGUP=/home/sangbum/drone_ws/bringup
export PYTHONPATH="/home/sangbum/drone_ws/external/Cosys-AirSim/PythonClient:$PYTHONPATH"
