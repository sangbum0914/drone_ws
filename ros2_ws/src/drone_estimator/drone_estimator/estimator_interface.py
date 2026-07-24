"""State estimator 추상 인터페이스 — 자작 estimator를 꽂는 교체 지점.

이 인터페이스만 구현하면 estimator_node 가 센서를 먹여주고 결과를 발행한다.
시뮬레이터(AirSim/Gazebo/JSBSim)가 바뀌어도 이 인터페이스는 불변.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ImuSample:
    """IMU 측정 한 샘플 (body frame)."""

    t_sec: float
    ang_vel: tuple[float, float, float]  # rad/s (wx, wy, wz)
    lin_acc: tuple[float, float, float]  # m/s^2 (ax, ay, az)


@dataclass
class GnssSample:
    """GNSS 측정 한 샘플."""

    t_sec: float
    lat: float
    lon: float
    alt: float
    # ENU local 좌표(변환 완료값)를 함께 실어 estimator 편의 제공 (없으면 None)
    enu: tuple[float, float, float] | None = None


@dataclass
class CameraSample:
    """카메라 프레임 한 장 (front-end 입력)."""

    t_sec: float
    width: int
    height: int
    encoding: str
    data: bytes = field(repr=False)
    # 카메라 intrinsics (fx, fy, cx, cy)
    intrinsics: tuple[float, float, float, float] | None = None


@dataclass
class StateEstimate:
    """estimator 출력 상태 (world/ENU frame)."""

    t_sec: float
    position: tuple[float, float, float]           # x, y, z
    orientation: tuple[float, float, float, float]  # quaternion (x, y, z, w)
    velocity: tuple[float, float, float] = (0.0, 0.0, 0.0)
    # 6x6 pose covariance (row-major, position+orientation) — consistency 평가용
    pose_covariance: list[float] | None = None


class StateEstimatorBase(ABC):
    """자작 estimator 가 상속할 베이스 클래스.

    estimator_node 는 센서 콜백에서 on_imu/on_gnss/on_camera 를 호출하고,
    주기적으로 get_estimate 를 호출해 결과를 발행한다.
    구현체는 스레드 안전을 스스로 보장할 것.
    """

    @abstractmethod
    def on_imu(self, sample: ImuSample) -> None:
        """IMU 샘플 수신 시 호출 (보통 최고 주파수 → propagation)."""

    @abstractmethod
    def on_gnss(self, sample: GnssSample) -> None:
        """GNSS 샘플 수신 시 호출 (update)."""

    @abstractmethod
    def on_camera(self, sample: CameraSample) -> None:
        """카메라 프레임 수신 시 호출 (visual front-end → update)."""

    @abstractmethod
    def get_estimate(self) -> StateEstimate | None:
        """현재 최적 상태 추정을 반환. 아직 초기화 전이면 None."""

    def reset(self) -> None:
        """에피소드 리셋 시 재초기화 (adapter 계약의 reset semantics)."""
        return None
