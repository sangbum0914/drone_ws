"""임시 IMU dead-reckoning stub estimator.

배관(파이프라인)이 살아있는지 검증하기 위한 자리표시자.
실제 검증에서는 이 클래스를 당신의 estimator 구현으로 교체한다.
GNSS 로 위치를 리셋하고 IMU accel 을 이중 적분하는 아주 단순한 모델.
"""

import math
import threading

from .estimator_interface import (
    CameraSample,
    GnssSample,
    ImuSample,
    StateEstimate,
    StateEstimatorBase,
)


class DeadReckoningStub(StateEstimatorBase):
    """IMU 이중적분 + GNSS 위치 스냅 (자리표시자용)."""

    def __init__(self, gravity: float = 9.80665) -> None:
        self._lock = threading.Lock()
        self._g = gravity
        self._t_prev: float | None = None
        self._pos = [0.0, 0.0, 0.0]
        self._vel = [0.0, 0.0, 0.0]
        self._quat = (0.0, 0.0, 0.0, 1.0)  # 회전 미추정(자리표시자)
        self._initialized = False

    def on_imu(self, sample: ImuSample) -> None:
        with self._lock:
            if self._t_prev is None:
                self._t_prev = sample.t_sec
                return
            dt = sample.t_sec - self._t_prev
            self._t_prev = sample.t_sec
            if dt <= 0.0 or dt > 0.5:
                return
            # 매우 단순: world accel ≈ body accel - g (회전 무시, 자리표시자)
            ax, ay, az = sample.lin_acc
            acc_w = [ax, ay, az - self._g]
            for i in range(3):
                self._pos[i] += self._vel[i] * dt + 0.5 * acc_w[i] * dt * dt
                self._vel[i] += acc_w[i] * dt

    def on_gnss(self, sample: GnssSample) -> None:
        with self._lock:
            if sample.enu is not None:
                # GNSS 위치로 스냅 (드리프트 리셋)
                self._pos = list(sample.enu)
                self._initialized = True

    def on_camera(self, sample: CameraSample) -> None:
        # 자리표시자: 카메라 미사용
        return None

    def get_estimate(self) -> StateEstimate | None:
        with self._lock:
            if not self._initialized or self._t_prev is None:
                return None
            if any(math.isnan(v) for v in self._pos):
                return None
            return StateEstimate(
                t_sec=self._t_prev,
                position=(self._pos[0], self._pos[1], self._pos[2]),
                orientation=self._quat,
                velocity=(self._vel[0], self._vel[1], self._vel[2]),
            )

    def reset(self) -> None:
        with self._lock:
            self._t_prev = None
            self._pos = [0.0, 0.0, 0.0]
            self._vel = [0.0, 0.0, 0.0]
            self._initialized = False
