# Phase 5 — 커스텀 Fixed-wing 캠페인 (별도)

## 목표
커스텀 fixed-wing 기체를 공력까지 직접 설계해 JSBSim에 인코딩하고,
PX4 제어 + AirSim 렌더로 estimator를 새 동역학 하에서 검증.
**quad 검증의 연장이 아닌 신규 검증 캠페인.**

## 공력 설계 파이프라인
```
[기하/에어포일 설계]
      ↓
[XFLR5 / AVL]  ── VLM/패널법 → CL, CD, Cm, 안정 미계수
      ↓
[JSBSim XML]   ── 공력계수 테이블 인코딩 (6-DOF FDM)
      ↓
[PX4 SITL]     ── fixed-wing 제어 (JSBSim bridge)
      ↓
[AirSim]       ── ExternalPhysicsEngine pose-slaved 렌더 + 카메라
```

- JSBSim XML = 렌더러 무관 **이식 가능한 기체 원본**.
- (참고) PX4 Gazebo 경로는 AVL Automation Tool → Advanced-Lift-Drag SDF지만
  Gazebo 전용이라 여기선 JSBSim으로 표준화.

## fixed-wing 특유 고려
- 전진 비행·받음각·실속 영역에서 카메라/GNSS/IMU 기하가 quad와 상이.
- 이착륙·선회·순항 등 비행 영역별 estimator 거동 검증.
- 제어 튜닝(경로추종, TECS 등)은 PX4 파라미터 재튜닝 필요.

## 통과 기준
- [ ] JSBSim fixed-wing이 PX4 제어로 순항/선회 안정
- [ ] 공력 모델 sanity (실속·트림 거동 물리적)
- [ ] estimator가 fixed-wing 비행 영역에서 목표 정확도
- [ ] conformance test 통과

## 산출물
- 커스텀 기체 XFLR5/AVL 프로젝트 + JSBSim XML
- fixed-wing PX4 파라미터셋
- fixed-wing estimator 검증 리포트
