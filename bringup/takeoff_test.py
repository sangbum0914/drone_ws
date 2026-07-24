#!/usr/bin/env python3
"""PX4 quad 이륙 스모크 테스트 (ROS2 /fmu/in/vehicle_command 경유).

시퀀스: AUTO.TAKEOFF 모드 설정 → arm → hover 관찰 → AUTO.LAND.
고도는 /fmu/out/vehicle_local_position(z, NED) 와 GT(/airsim_node/.../odom_local) 로 관찰.
NED↔ENU 부호 검증도 겸함 (이륙 시 PX4 z 감소(위=−), ENU GT z 증가 기대).
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy
from px4_msgs.msg import VehicleCommand, VehicleLocalPosition


def px4_qos() -> QoSProfile:
    """PX4 uXRCE-DDS 호환 QoS (best_effort)."""
    return QoSProfile(
        reliability=ReliabilityPolicy.BEST_EFFORT,
        durability=DurabilityPolicy.VOLATILE,
        history=HistoryPolicy.KEEP_LAST,
        depth=10,
    )


class TakeoffTest(Node):
    def __init__(self) -> None:
        super().__init__("takeoff_test")
        qos = px4_qos()
        self._cmd_pub = self.create_publisher(
            VehicleCommand, "/fmu/in/vehicle_command", qos
        )
        self.create_subscription(
            VehicleLocalPosition,
            "/fmu/out/vehicle_local_position_v1",
            self._on_lpos,
            qos,
        )
        self._z = None
        self._z0 = None
        self._t = 0
        self._armed_sent = False
        self._land_sent = False
        # 100ms 주기 상태머신
        self.create_timer(0.1, self._tick)

    def _on_lpos(self, msg: VehicleLocalPosition) -> None:
        self._z = msg.z  # NED: 위로 갈수록 감소(음수)

    def _send(self, command: int, p1: float = 0.0, p2: float = 0.0,
              p3: float = 0.0) -> None:
        m = VehicleCommand()
        m.timestamp = int(self.get_clock().now().nanoseconds / 1000)
        m.command = command
        m.param1 = p1
        m.param2 = p2
        m.param3 = p3
        m.target_system = 1
        m.target_component = 1
        m.source_system = 1
        m.source_component = 1
        m.from_external = True
        self._cmd_pub.publish(m)

    def _tick(self) -> None:
        self._t += 1
        # t=1.0s: AUTO.TAKEOFF 모드 (main=4 AUTO, sub=2 TAKEOFF)
        if self._t == 10:
            self.get_logger().info("모드 → AUTO.TAKEOFF")
            # base_mode=CUSTOM(1), main_mode=AUTO(4), sub_mode=TAKEOFF(2)
            self._send(VehicleCommand.VEHICLE_CMD_DO_SET_MODE, 1.0, 4.0, 2.0)
            self._send(VehicleCommand.VEHICLE_CMD_DO_SET_MODE, 1.0, 4.0, 2.0)
        # t=2.0s: arm
        if self._t == 20 and not self._armed_sent:
            self.get_logger().info("ARM 전송")
            self._send(VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM, 1.0)
            self._armed_sent = True
            if self._z is not None:
                self._z0 = self._z
        # 고도 로깅
        if self._t % 10 == 0 and self._z is not None:
            rel = (self._z0 - self._z) if self._z0 is not None else 0.0
            self.get_logger().info(
                f"t={self._t/10:.0f}s  PX4 z(NED)={self._z:+.2f}m  상승={rel:+.2f}m"
            )
        # t=18s: 착륙
        if self._t == 180 and not self._land_sent:
            self.get_logger().info("AUTO.LAND 전송")
            self._send(VehicleCommand.VEHICLE_CMD_NAV_LAND)
            self._land_sent = True
        if self._t >= 240:
            self.get_logger().info("테스트 종료")
            rclpy.shutdown()


def main() -> None:
    rclpy.init()
    node = TakeoffTest()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, Exception):
        pass


if __name__ == "__main__":
    main()
