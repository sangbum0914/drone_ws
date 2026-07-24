"""estimator + evaluator 를 함께 띄우는 런치.

사용:
  ros2 launch drone_estimator estimator.launch.py \
      config:=<config yaml 경로> use_sim_time:=true
adapter 계약: use_sim_time 필수(=true) — sim clock 권위.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    config = LaunchConfiguration("config")
    use_sim_time = LaunchConfiguration("use_sim_time")

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "config",
                default_value="",
                description="토픽/estimator 파라미터 yaml (비우면 노드 기본값)",
            ),
            DeclareLaunchArgument(
                "use_sim_time",
                default_value="true",
                description="sim clock 사용 (adapter 계약상 true 강제 권장)",
            ),
            Node(
                package="drone_estimator",
                executable="estimator_node",
                name="estimator_node",
                output="screen",
                parameters=[
                    config,
                    {"use_sim_time": use_sim_time},
                ],
            ),
            Node(
                package="drone_estimator",
                executable="evaluator_node",
                name="evaluator_node",
                output="screen",
                parameters=[
                    config,
                    {"use_sim_time": use_sim_time},
                ],
            ),
        ]
    )
