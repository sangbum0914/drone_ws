#!/usr/bin/env python3
"""전용 Ground-Truth 발행 노드 — AirSim RPC(경량)로 GT 폴링 → ENU 발행.

airsim_node 의 불안정한 odom 루프를 우회. 독립 RPC 연결로 simGetGroundTruthKinematics
를 50Hz 폴링하여 /drone/gt/pose (ENU) 발행. evaluator 가 이걸 GT 로 사용.
AirSim 은 NED → ENU 로 변환: (E,N,U) = (ned.y, ned.x, -ned.z).
"""
import sys
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSPresetProfiles
from geometry_msgs.msg import PoseStamped

sys.path.insert(0, "/home/sangbum/drone_ws/external/Cosys-AirSim/PythonClient")
import cosysairsim as airsim  # noqa: E402


class GtPublisher(Node):
    def __init__(self) -> None:
        super().__init__("gt_publisher")
        self.declare_parameter("rate_hz", 50.0)
        self.declare_parameter("vehicle", "Drone1")
        self._pub = self.create_publisher(
            PoseStamped, "/drone/gt/pose", QoSPresetProfiles.SENSOR_DATA.value
        )
        self._veh = self.get_parameter("vehicle").value
        self._c = airsim.MultirotorClient(ip="127.0.0.1", port=41451, timeout_value=5)
        self._c.confirmConnection()
        self.get_logger().info("GT publisher: AirSim RPC 연결 완료")
        rate = float(self.get_parameter("rate_hz").value)
        self.create_timer(1.0 / rate, self._tick)
        self._fail = 0

    def _tick(self) -> None:
        try:
            k = self._c.simGetGroundTruthKinematics(vehicle_name=self._veh)
        except Exception as e:  # RPC 일시 실패는 흘려보냄
            self._fail += 1
            if self._fail % 50 == 1:
                self.get_logger().warn(f"RPC 실패({self._fail}): {e}")
            return
        p = k.position
        o = k.orientation
        m = PoseStamped()
        m.header.stamp = self.get_clock().now().to_msg()
        m.header.frame_id = "map"
        # NED → ENU (위치)
        m.pose.position.x = p.y_val
        m.pose.position.y = p.x_val
        m.pose.position.z = -p.z_val
        # 방향: NED→ENU 근사 (x<->y, z 부호). ATE 위치 평가엔 위치가 핵심.
        m.pose.orientation.x = o.y_val
        m.pose.orientation.y = o.x_val
        m.pose.orientation.z = -o.z_val
        m.pose.orientation.w = o.w_val
        self._pub.publish(m)


def main() -> None:
    rclpy.init()
    n = GtPublisher()
    try:
        rclpy.spin(n)
    except KeyboardInterrupt:
        pass
    finally:
        rclpy.shutdown()


if __name__ == "__main__":
    main()
