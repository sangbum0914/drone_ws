#!/usr/bin/env python3
"""PX4 offboard 키보드 teleop — 드론을 키보드로 속도/자세 제어.

⚠️ 반드시 실제 터미널에서 실행할 것 (키 입력에 TTY 필요):
    source ~/drone_ws/bringup/env.sh
    python3 ~/drone_ws/bringup/keyboard_teleop.py

동작: offboard 셋포인트를 계속 스트리밍하며, T 를 누르면 arm+offboard 진입.
속도는 body frame → NED 로 현재 heading 기준 회전(직관적 조종).

키 매핑:
    T : arm + offboard 진입 (이륙 준비)
    W/S : 전진/후진        A/D : 좌/우 (body)
    R/F : 상승/하강        Q/E : yaw rate 증감(누를 때마다 ±0.2, 최대 ±2.0)
    Space : 정지(hover, yaw 포함)  L : 착륙(AUTO.LAND)
    +/- : 속도 스케일 증감
    Ctrl-C : 종료
"""

import math
import sys
import select
import termios
import tty
import threading

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy
from px4_msgs.msg import (
    OffboardControlMode,
    TrajectorySetpoint,
    VehicleCommand,
    VehicleLocalPosition,
)

HELP = __doc__


def px4_qos() -> QoSProfile:
    return QoSProfile(
        reliability=ReliabilityPolicy.BEST_EFFORT,
        durability=DurabilityPolicy.VOLATILE,
        history=HistoryPolicy.KEEP_LAST,
        depth=10,
    )


class KeyboardTeleop(Node):
    def __init__(self) -> None:
        super().__init__("keyboard_teleop")
        qos = px4_qos()
        self._ocm_pub = self.create_publisher(OffboardControlMode, "/fmu/in/offboard_control_mode", qos)
        self._sp_pub = self.create_publisher(TrajectorySetpoint, "/fmu/in/trajectory_setpoint", qos)
        self._cmd_pub = self.create_publisher(VehicleCommand, "/fmu/in/vehicle_command", qos)
        self.create_subscription(VehicleLocalPosition, "/fmu/out/vehicle_local_position_v1", self._on_lpos, qos)

        # body-frame 목표 속도(m/s) + yaw rate(rad/s)
        self.vx = self.vy = self.vz = 0.0
        self.yaw_rate = 0.0
        self.scale = 1.5          # 속도 스케일
        self.heading = 0.0        # 현재 yaw(rad, NED)
        self.z = 0.0
        self._offboard = False
        self._n = 0

        # 20Hz 로 offboard heartbeat + 셋포인트 스트리밍 (offboard 유지 필수)
        self.create_timer(0.05, self._stream)

    def _on_lpos(self, m: VehicleLocalPosition) -> None:
        self.heading = m.heading
        self.z = m.z

    def _cmd(self, command: int, p1=0.0, p2=0.0, p3=0.0) -> None:
        c = VehicleCommand()
        c.timestamp = int(self.get_clock().now().nanoseconds / 1000)
        c.command = command
        c.param1, c.param2, c.param3 = p1, p2, p3
        c.target_system = 1
        c.target_component = 1
        c.source_system = 1
        c.source_component = 1
        c.from_external = True
        self._cmd_pub.publish(c)

    def _stream(self) -> None:
        # 1) offboard control mode heartbeat (velocity)
        ocm = OffboardControlMode()
        ocm.timestamp = int(self.get_clock().now().nanoseconds / 1000)
        ocm.position = False
        ocm.velocity = True
        ocm.acceleration = False
        ocm.attitude = False
        ocm.body_rate = False
        self._ocm_pub.publish(ocm)

        # 2) body → NED 속도 회전 (heading 기준)
        c, s = math.cos(self.heading), math.sin(self.heading)
        vn = self.vx * c - self.vy * s
        ve = self.vx * s + self.vy * c
        vd = -self.vz  # 위(+vz) = NED 아래(-)

        sp = TrajectorySetpoint()
        sp.timestamp = int(self.get_clock().now().nanoseconds / 1000)
        sp.position = [float("nan")] * 3
        sp.velocity = [vn, ve, vd]
        sp.acceleration = [float("nan")] * 3
        sp.jerk = [float("nan")] * 3
        sp.yaw = float("nan")
        sp.yawspeed = self.yaw_rate
        self._sp_pub.publish(sp)

    def arm_offboard(self) -> None:
        # offboard(custom main mode 6) + arm
        self._cmd(VehicleCommand.VEHICLE_CMD_DO_SET_MODE, 1.0, 6.0)
        self._cmd(VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM, 1.0)
        self._offboard = True
        self.get_logger().info("ARM + OFFBOARD 진입")

    def land(self) -> None:
        self._cmd(VehicleCommand.VEHICLE_CMD_NAV_LAND)
        self.vx = self.vy = self.vz = self.yaw_rate = 0.0
        self.get_logger().info("AUTO.LAND")

    def handle_key(self, k: str) -> None:
        v = self.scale
        if k == "t":
            self.arm_offboard()
        elif k == "l":
            self.land()
        elif k == "w":
            self.vx = v
        elif k == "s":
            self.vx = -v
        elif k == "a":
            self.vy = -v
        elif k == "d":
            self.vy = v
        elif k == "r":
            self.vz = v
        elif k == "f":
            self.vz = -v
        elif k == "q":
            self.yaw_rate = max(-2.0, self.yaw_rate - 0.2)  # 좌 yaw 증가(누를 때마다)
        elif k == "e":
            self.yaw_rate = min(2.0, self.yaw_rate + 0.2)   # 우 yaw 증가(누를 때마다)
        elif k == " ":
            self.vx = self.vy = self.vz = self.yaw_rate = 0.0
        elif k == "+":
            self.scale = min(5.0, self.scale + 0.5)
        elif k == "-":
            self.scale = max(0.5, self.scale - 0.5)


def key_loop(node: KeyboardTeleop) -> None:
    """터미널 raw 모드로 키를 읽어 노드에 전달."""
    print(HELP)
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        while rclpy.ok():
            if select.select([sys.stdin], [], [], 0.1)[0]:
                k = sys.stdin.read(1)
                if k == "\x03":  # Ctrl-C
                    break
                node.handle_key(k.lower())
                sys.stdout.write(
                    f"\rv=({node.vx:+.1f},{node.vy:+.1f},{node.vz:+.1f}) "
                    f"yaw_rate={node.yaw_rate:+.1f} scale={node.scale:.1f} "
                    f"alt={-node.z:+.2f}m   "
                )
                sys.stdout.flush()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def main() -> None:
    rclpy.init()
    node = KeyboardTeleop()
    spin = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    spin.start()
    try:
        key_loop(node)
    except KeyboardInterrupt:
        pass
    finally:
        rclpy.shutdown()


if __name__ == "__main__":
    main()
