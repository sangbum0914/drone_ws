# drone_ws — 드론 시뮬레이션 기반 자작 State Estimator 검증

PX4 SITL + Unreal Engine 5.8 + Cosys-AirSim + ROS 2 (Jazzy) 스택 위에서
자작 state estimator(camera + GNSS + IMU 융합)를 검증하고, 추정값 기반 제어,
그리고 JSBSim 커스텀 기체까지 확장하는 프로젝트.

## 구조
```
design/        아키텍처 결정·5단계 로드맵·adapter 계약 문서
bringup/       스택 기동/검증 스크립트 (env·start_stack·verify_stack)
ros2_ws/src/
  drone_estimator/   estimator 교체 인터페이스 + 노드 + evaluator (ROS2 파이썬 패키지)
sim/airsim/    AirSim lockstep settings.json
external/      (git 제외) 대용량 의존성 — 아래 참조
```

## 설계 문서
- [design/00_overview.md](design/00_overview.md) — 아키텍처·시뮬레이터 선정 근거·로드맵
- [design/01_adapter_contract.md](design/01_adapter_contract.md) — ROS2 sim-adapter conformance 계약
- `design/phase0~5_*.md` — 단계별 계획

## 아키텍처 요지
- **AirSim(UE5) 렌더 + PX4 SITL 제어 + lockstep**. 자작 모듈은 ROS2 표준 메시지 뒤 adapter로 연결 → estimator·sim 모두 교체 가능.
- 커스텀 기체 공력은 **JSBSim**에 표준화(렌더러 무관 이식). Gazebo Harmonic은 무료 fallback.

## 외부 의존성 (git 미포함, 직접 설치)
`external/` 에 배치:
- **PX4-Autopilot** (SITL): `git clone --recursive https://github.com/PX4/PX4-Autopilot`
- **Unreal Engine 5.8** (Linux, Epic 계정): unrealengine.com/en-US/linux
- **Cosys-AirSim**: `git clone https://github.com/Cosys-Lab/Cosys-AirSim` → `./setup.sh` → `./build.sh --ue-root <UE>`
- **px4_msgs** (ros2_ws/src): `git clone https://github.com/PX4/px4_msgs` (PX4 버전 일치)
- **Micro-XRCE-DDS-Agent**: eProsima, 소스 빌드

### 빌드 트러블슈팅 노트
- Cosys-AirSim + UE clang + Ubuntu 24.04(glibc≥2.38)에서 rpclib `pthread_cond_clockwait` 미스매치 →
  UE clang을 `-stdlib=libc++`로 감싸는 wrapper 사용(`external/ue_clang_wrapper/`).

## 실행
```bash
bash bringup/start_stack.sh     # AirSim→PX4→agent→airsim_node 순 기동
bash bringup/verify_stack.sh    # 프로세스+토픽 흐름 검증
```
> ⚠️ `/fmu/*` 토픽 확인 시 반드시 `bringup/env.sh`로 **px4_msgs(ros2_ws)를 소싱**할 것.
> 미소싱 시 역직렬화 실패로 "무응답"으로 보임(데이터는 정상).

## estimator 교체
`ros2_ws/src/drone_estimator/estimator_interface.py`의 `StateEstimatorBase`를 상속 구현하고,
`config/topics_airsim.yaml`의 `estimator_class`에 지정하면 파이프라인에 연결됨.
