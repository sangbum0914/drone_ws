# Phase 4 — JSBSim Quad로 백엔드 통합 Shake-out

## 목표
fixed-wing으로 바로 점프하지 않고, **이미 검증된 quad 동역학**으로
JSBSim+PX4+AirSim `ExternalPhysicsEngine` **백엔드 통합**을 먼저 안정화. (codex 권고)

## 왜 quad 브리지인가
Phase 5(커스텀 fixed-wing)는 두 위험을 동시에 안음: ①새 백엔드 통합 ②새 공력/기체.
quad(동역학 기지)로 ①을 먼저 격리 해결하면, Phase 5는 ②에만 집중 가능.
(VTOL은 전이모드 리스크라 브리지로 부적합 → quad 사용.)

## 브리지 소유권 (명확히)
AirSim `ExternalPhysicsEngine`는 vehicle를 **pose-slave**만 함. 브리지가 다음을 **소유**:
- **Master clock** + JSBSim 스텝 진행
- **PX4 ↔ JSBSim 센서/액추에이터 교환** (HIL_SENSOR / HIL_ACTUATOR_CONTROLS)
- **충돌(collision) 피드백**
- AirSim엔 `simSetVehiclePose`로 pose 주입, 카메라/센서는 AirSim에서 취득

## 센서 출처 규약
- IMU/GNSS = **JSBSim/PX4** (AirSim pose 미분 금지)
- 카메라 = **AirSim** (photorealistic)

## 통과 기준
- [ ] JSBSim quad가 PX4 제어로 안정 비행 (AirSim 렌더)
- [ ] conformance test 재통과 (신규 백엔드 — 특히 clock/lockstep/ENU↔NED)
- [ ] Phase 1~3 estimator/제어 모듈 **무수정** 동작 (adapter만 교체)
- [ ] pose-slave 지연·정합 검증

## 산출물
- `jsbsim_bridge/` (clock·스텝·PX4 교환·AirSim pose 주입)
- JSBSim quad 모델
- 신규 백엔드 conformance 리포트
