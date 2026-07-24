# Phase 0 — AirSim + PX4 Lockstep 브링업 (게이트)

## 목표
이후 모든 검증의 토대인 **AirSim + PX4 SITL lockstep 파이프라인**을 세우고,
그 **타이밍·센서 안정성을 게이트로 통과**시킨다. 실패하면 Gazebo fallback으로 전환.

## 왜 게이트인가
AirSim+PX4 lockstep은 존재하지만 실무 셋업이 까다로움(타임아웃, 무거운 센서 시 jerkiness,
default barometer/IMU 노이즈 과다 → 클램프 필요). estimator를 올리기 전에 **토대가 결정론적·안정적인지 먼저 확증**해야 한다.

## 작업 항목
1. **의존성 설치**
   - PX4-Autopilot 클론 + 빌드 (`make px4_sitl none_iris` 등)
   - Cosys-AirSim 클론 + UE5 (5.x) + AirSim 플러그인 빌드
   - ROS2 Jazzy: AirSim ROS2 wrapper, PX4 uXRCE-DDS agent
2. **lockstep 설정** (`settings.json`)
   - `"ClockType": "SteppableClock"`, `"PhysicsEngineName"` 기본, PX4 vehicle: `UseTcp=true`, `LockStep=true`
   - barometer/IMU 노이즈 클램프
3. **quad(x500/iris) 이륙 → hover → 착륙** 최소 시나리오 실행
4. **conformance test 실행** ([01_adapter_contract.md](01_adapter_contract.md))

## 통과 기준 (Gate)
- [ ] PX4 SITL ↔ AirSim lockstep 연결 안정 (타임아웃 없이 수 분 hover)
- [ ] `/clock` 단조 증가, 모든 노드 `use_sim_time=true`
- [ ] IMU/GNSS/카메라 토픽 발행 + 스탬프 단조·지터 한계 내
- [ ] hover 시 IMU accel 부호 정확 (NED 확인)
- [ ] 동일 시나리오 2회 → GT 궤적 근사 일치 (반복성)
- [ ] GT pose 토픽 확보

## 실패 시
- Gazebo(`make px4_sitl gz_x500`)로 전환, 동일 conformance test.
- 카메라 검증은 별도로 미룸(Gazebo 비사실적).

## 산출물
- `sim/airsim/settings.json`
- `bringup/` 실행 스크립트/런치
- conformance test 리포트
