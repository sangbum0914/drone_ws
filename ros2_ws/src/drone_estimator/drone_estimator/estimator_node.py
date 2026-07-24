"""Estimator ROS2 노드 — 표준 센서 토픽을 받아 자작 estimator 에 먹이고 odom 발행.

adapter 계약: 표준 메시지(sensor_msgs/Imu, NavSatFix, Image)만 구독하고
결과는 nav_msgs/Odometry 로 발행. 시뮬레이터 종속 없음(토픽 remap 으로 연결).
estimator 구현은 파라미터 'estimator_class'로 동적 로드 → 교체 지점.
"""

import importlib
import math

import rclpy
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.qos import QoSPresetProfiles
from sensor_msgs.msg import Image, Imu, NavSatFix

from .estimator_interface import (
    CameraSample,
    GnssSample,
    ImuSample,
    StateEstimatorBase,
)

# WGS84
_A = 6378137.0
_E2 = 6.69437999014e-3


def _geodetic_to_enu(lat, lon, alt, ref):
    """간단 ENU 변환 (기준점 대비 local tangent plane)."""
    lat_r, lon_r, alt_r = ref
    lat0 = math.radians(lat_r)
    lon0 = math.radians(lon_r)
    d_lat = math.radians(lat - lat_r)
    d_lon = math.radians(lon - lon_r)
    m = _A * (1 - _E2) / (1 - _E2 * math.sin(lat0) ** 2) ** 1.5
    n = _A / math.sqrt(1 - _E2 * math.sin(lat0) ** 2)
    east = d_lon * (n * math.cos(lat0))
    north = d_lat * m
    up = alt - alt_r
    return (east, north, up)


def _load_estimator(class_path: str) -> StateEstimatorBase:
    """'module.submodule:ClassName' 문자열로 estimator 동적 로드."""
    mod_name, _, cls_name = class_path.partition(":")
    module = importlib.import_module(mod_name)
    cls = getattr(module, cls_name)
    return cls()


class EstimatorNode(Node):
    """센서 → estimator → odom 파이프라인 노드."""

    def __init__(self) -> None:
        super().__init__("estimator_node")

        # 교체 지점: 기본은 dead-reckoning stub. 자작 estimator 로 바꿔 지정.
        default_est = "drone_estimator.dead_reckoning_stub:DeadReckoningStub"
        self.declare_parameter("estimator_class", default_est)
        self.declare_parameter("imu_topic", "/drone/imu")
        self.declare_parameter("gnss_topic", "/drone/gnss")
        self.declare_parameter("camera_topic", "/drone/cam/image")
        self.declare_parameter("odom_topic", "/estimator/odom")
        self.declare_parameter("publish_rate_hz", 50.0)
        self.declare_parameter("odom_frame", "map")
        self.declare_parameter("child_frame", "base_link")

        est_class = self.get_parameter("estimator_class").value
        self._estimator = _load_estimator(est_class)
        self.get_logger().info(f"estimator 로드: {est_class}")

        self._gnss_ref: tuple[float, float, float] | None = None

        sensor_qos = QoSPresetProfiles.SENSOR_DATA.value
        self.create_subscription(
            Imu, self.get_parameter("imu_topic").value, self._on_imu, sensor_qos
        )
        self.create_subscription(
            NavSatFix,
            self.get_parameter("gnss_topic").value,
            self._on_gnss,
            sensor_qos,
        )
        self.create_subscription(
            Image,
            self.get_parameter("camera_topic").value,
            self._on_camera,
            sensor_qos,
        )
        self._odom_pub = self.create_publisher(
            Odometry, self.get_parameter("odom_topic").value, 10
        )

        rate = float(self.get_parameter("publish_rate_hz").value)
        self.create_timer(1.0 / rate, self._publish_estimate)

    # --- 센서 콜백 ---
    def _on_imu(self, msg: Imu) -> None:
        t = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        self._estimator.on_imu(
            ImuSample(
                t_sec=t,
                ang_vel=(
                    msg.angular_velocity.x,
                    msg.angular_velocity.y,
                    msg.angular_velocity.z,
                ),
                lin_acc=(
                    msg.linear_acceleration.x,
                    msg.linear_acceleration.y,
                    msg.linear_acceleration.z,
                ),
            )
        )

    def _on_gnss(self, msg: NavSatFix) -> None:
        t = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        if self._gnss_ref is None:
            self._gnss_ref = (msg.latitude, msg.longitude, msg.altitude)
        enu = _geodetic_to_enu(
            msg.latitude, msg.longitude, msg.altitude, self._gnss_ref
        )
        self._estimator.on_gnss(
            GnssSample(
                t_sec=t,
                lat=msg.latitude,
                lon=msg.longitude,
                alt=msg.altitude,
                enu=enu,
            )
        )

    def _on_camera(self, msg: Image) -> None:
        t = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        self._estimator.on_camera(
            CameraSample(
                t_sec=t,
                width=msg.width,
                height=msg.height,
                encoding=msg.encoding,
                data=bytes(msg.data),
            )
        )

    # --- 발행 ---
    def _publish_estimate(self) -> None:
        est = self._estimator.get_estimate()
        if est is None:
            return
        odom = Odometry()
        odom.header.stamp = self.get_clock().now().to_msg()
        odom.header.frame_id = self.get_parameter("odom_frame").value
        odom.child_frame_id = self.get_parameter("child_frame").value
        odom.pose.pose.position.x = est.position[0]
        odom.pose.pose.position.y = est.position[1]
        odom.pose.pose.position.z = est.position[2]
        odom.pose.pose.orientation.x = est.orientation[0]
        odom.pose.pose.orientation.y = est.orientation[1]
        odom.pose.pose.orientation.z = est.orientation[2]
        odom.pose.pose.orientation.w = est.orientation[3]
        odom.twist.twist.linear.x = est.velocity[0]
        odom.twist.twist.linear.y = est.velocity[1]
        odom.twist.twist.linear.z = est.velocity[2]
        if est.pose_covariance is not None and len(est.pose_covariance) == 36:
            odom.pose.covariance = est.pose_covariance
        self._odom_pub.publish(odom)


def main() -> None:
    rclpy.init()
    node = EstimatorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
