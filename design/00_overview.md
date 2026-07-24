# 00. 드론 시뮬레이션 프로젝트 — 아키텍처 개요

> **최종 결정 (2026-07-23): AirSim + Unreal Engine 경로 확정.**
> UE 상업 라이선스(연매출 $1M 초과 회사 → seat당 $1,850/년)를 검토한 뒤, 사용자가 UE 경로 진행을 결정
> (라이선스는 NAVER LABS 측에서 처리/감수). photorealism 확보 우선. 본문의 "AirSim-first" 서술이 유효.
> Gazebo Harmonic 8.14 도 설치돼 있어 **무료 fallback / 교차검증용**으로 상비.
> (한때 라이선스 우려로 PX4+Gazebo 오픈경로로 전환했다가 UE로 복귀함.)

## 목적
자작 **state estimator**(camera + GNSS + IMU 융합)를 시뮬레이션에서 검증하고,
추정값 기반 제어를 실험한 뒤, 커스텀 기체(공력 포함)까지 확장한다.

## 최종 결정 (codex 교차검증 다라운드 합의)

### 시뮬레이터: AirSim-first + PX4 SITL
- **AirSim(UE5)** 을 주력으로. quad 단계부터 AirSim에서 수행.
  - 이유 ① AirSim이 최종 타깃 → Gazebo→AirSim 포팅 불연속 제거
  - 이유 ② estimator가 카메라 기반 → **photorealism 필수** (Gazebo 비사실적 카메라론 VIO 프론트엔드 검증 불가)
  - 이유 ③ AirSim도 **PX4 lockstep**(SteppableClock, `UseTcp=true`, `LockStep=true`) 지원 → 결정론/타임스탬프 우려 해소
- **PX4 SITL** 이 자세/위치 제어 담당 (MAVLink lockstep).
- **Gazebo** = 강제 아님. 상비 **fallback** + 순수 필터수학 결정론 레퍼런스(완벽/합성 특징)로만 유지.

### AirSim 계열 선택
| 후보 | 상태 | 판정 |
|---|---|---|
| 원조 AirSim (Microsoft) | archived (2022) | ✗ |
| Colosseum (CodexLabsLLC) | archived (2026-07-11) | ✗ |
| **Cosys-AirSim** (Univ. Antwerp) | 활발, UE5, ROS2, 성숙 | ✅ **주력** |
| Project AirSim (iamaisim) | MIT, UE5.2/5.7, v0.2.0 young | 이관 타깃 |

### 탈락 사유
- **Gazebo**: photorealism 부족 (fallback으로만).
- **Isaac Sim / Pegasus**: Omniverse라 Unreal 아님 + VTOL 미지원(multirotor만) + RL 학습용 위주.

### 커스텀 기체 공력 = JSBSim에 표준화
- 공력은 게임엔진이 아니라 **JSBSim(오픈소스 FDM)** 이 담당.
- 파이프라인: **XFLR5/AVL**(공력계수) → **JSBSim XML** → **PX4 SITL**(제어) → **AirSim `ExternalPhysicsEngine`**(pose-slaved 렌더 + 카메라/센서).
- Gazebo Advanced-Lift-Drag SDF는 Gazebo 전용 → 이식 불가. JSBSim XML은 렌더러 무관 이식 가능.
- **Simulink 배제**: MATLAB 유료 라이선스 필요.
- 턴키 대안: **PteroSim**(UE5+JSBSim+PX4, 학술무료 / 기업상업 라이선스 확인 필요).

## 확장 아키텍처 (모듈 갈아끼우기)

```
        ┌─ AirSim(UE5, NED) ──── photorealistic 렌더 + 카메라 ─┐
PX4 SITL┤  [Sim Adapter 계약]                                  │  ROS2 표준 토픽
(lockstep)  IMU/GNSS = PX4/JSBSim, camera = AirSim             ├──► estimator (자작)
        └─ (fallback) Gazebo, JSBSim ──────────────────────────┘    tracker / controller / evaluator
```

- 모든 자작 모듈 = **ROS2 노드 + 표준 메시지**(`sensor_msgs/Imu`, `Image`, `NavSatFix`, `nav_msgs/Odometry`).
- 시뮬레이터는 **얇은 adapter 계약** 뒤 → 모듈·sim 모두 swappable.
- adapter 계약 상세: [01_adapter_contract.md](01_adapter_contract.md)

## 5단계 로드맵

| 단계 | 문서 | 요약 |
|---|---|---|
| 0 | [phase0_lockstep_bringup.md](phase0_lockstep_bringup.md) | AirSim+PX4 lockstep 브링업 **게이트** |
| 1 | [phase1_estimator_openloop.md](phase1_estimator_openloop.md) | quad open-loop 추정 검증 |
| 2 | [phase2_shadow_mode.md](phase2_shadow_mode.md) | shadow-mode (EKF2 비행 중 병렬 비교) |
| 3 | [phase3_guarded_control.md](phase3_guarded_control.md) | guarded takeover 제어 |
| 4 | [phase4_jsbsim_airframe.md](phase4_jsbsim_airframe.md) | JSBSim quad로 백엔드 통합 shake-out |
| 5 | [phase5_fixedwing.md](phase5_fixedwing.md) | 커스텀 fixed-wing 별도 캠페인 |

## 환경
- 워크스테이션: RTX A6000 48GB, 드라이버 580.159.04
- OS/미들웨어: Linux, ROS2 **Jazzy**
- 워크스페이스: `/home/sangbum/drone_ws`
