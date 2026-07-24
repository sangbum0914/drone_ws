"""Evaluator 노드 — estimator odom 을 ground-truth 와 비교해 ATE/RPE 산출.

adapter 계약대로 표준 메시지만 사용:
  - estimator: nav_msgs/Odometry
  - ground truth: geometry_msgs/PoseStamped
종료 시 요약 통계를 로그로 출력.
"""

import bisect
import math

import rclpy
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.qos import QoSPresetProfiles


def _stamp(header) -> float:
    return header.stamp.sec + header.stamp.nanosec * 1e-9


class EvaluatorNode(Node):
    """estimator vs GT 오차(ATE/RPE) 평가."""

    def __init__(self) -> None:
        super().__init__("evaluator_node")
        self.declare_parameter("odom_topic", "/estimator/odom")
        self.declare_parameter("gt_topic", "/drone/gt/pose")
        self.declare_parameter("report_period_sec", 5.0)
        self.declare_parameter("rpe_delta_sec", 1.0)

        qos = QoSPresetProfiles.SENSOR_DATA.value
        self.create_subscription(
            Odometry, self.get_parameter("odom_topic").value, self._on_odom, qos
        )
        self.create_subscription(
            PoseStamped, self.get_parameter("gt_topic").value, self._on_gt, qos
        )

        # GT 시계열 버퍼 (시간정렬)
        self._gt_t: list[float] = []
        self._gt_p: list[tuple[float, float, float]] = []
        # 매칭된 (est, gt) 쌍
        self._pairs: list[tuple[float, tuple, tuple]] = []

        period = float(self.get_parameter("report_period_sec").value)
        self.create_timer(period, self._report)

    def _on_gt(self, msg: PoseStamped) -> None:
        t = _stamp(msg.header)
        p = (msg.pose.position.x, msg.pose.position.y, msg.pose.position.z)
        self._gt_t.append(t)
        self._gt_p.append(p)

    def _on_odom(self, msg: Odometry) -> None:
        if not self._gt_t:
            return
        t = _stamp(msg.header)
        p = (
            msg.pose.pose.position.x,
            msg.pose.pose.position.y,
            msg.pose.pose.position.z,
        )
        gt = self._nearest_gt(t)
        if gt is not None:
            self._pairs.append((t, p, gt))

    def _nearest_gt(self, t: float):
        """t 에 가장 가까운 GT 위치 (선형탐색 최소화)."""
        i = bisect.bisect_left(self._gt_t, t)
        cands = []
        if i < len(self._gt_t):
            cands.append(i)
        if i > 0:
            cands.append(i - 1)
        if not cands:
            return None
        best = min(cands, key=lambda k: abs(self._gt_t[k] - t))
        if abs(self._gt_t[best] - t) > 0.1:  # 100ms 이상 어긋나면 버림
            return None
        return self._gt_p[best]

    @staticmethod
    def _rmse(errs: list[float]) -> float:
        if not errs:
            return float("nan")
        return math.sqrt(sum(e * e for e in errs) / len(errs))

    def _report(self) -> None:
        if len(self._pairs) < 2:
            self.get_logger().info("평가 대기중 (매칭 쌍 부족)...")
            return
        # ATE: 위치 오차 노름의 RMSE (정렬 없이 raw — 동일 프레임 가정)
        ate_errs = [
            math.dist(p, gt) for _, p, gt in self._pairs
        ]
        ate = self._rmse(ate_errs)
        max_e = max(ate_errs)
        self.get_logger().info(
            f"[EVAL] pairs={len(self._pairs)}  "
            f"ATE(RMSE)={ate:.3f}m  max={max_e:.3f}m"
        )

    def destroy_node(self) -> bool:
        if self._pairs:
            ate = self._rmse([math.dist(p, gt) for _, p, gt in self._pairs])
            self.get_logger().info(
                f"[EVAL-FINAL] pairs={len(self._pairs)} ATE(RMSE)={ate:.3f}m"
            )
        return super().destroy_node()


def main() -> None:
    rclpy.init()
    node = EvaluatorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
