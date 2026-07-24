# Phase 1 — Quad Open-loop 추정 검증

## 목표
quadrotor에서 자작 **state estimator**를 **open-loop**로 돌려 GT 대비 정확도를 검증.
이 단계에서 estimator는 제어에 관여하지 않음 (PX4 EKF2가 비행).

## 접근
- AirSim+PX4로 quad 비행(다양한 궤적: hover, 사각, 8자, 공격적 기동).
- estimator 노드가 `/drone/imu`, `/drone/gnss`, `/drone/cam/image` 구독 → `/estimator/odom` 발행.
- evaluator가 `/estimator/odom` vs `/drone/gt/pose` 비교 → **ATE / RPE** 산출.

## estimator 버그 ↔ sim 아티팩트 격리 (codex 강조)
lockstep은 타이밍은 닫아도 **센서모델 fidelity는 보장 못 함**. 버그 원인 분리를 위해:
1. **Replay**: 기록한 rosbag으로 재현 가능한 회귀 테스트.
2. **합성/완벽 특징**: 카메라 프론트엔드를 배제하고 완벽한 랜드마크/대응으로 필터수학만 검증.
3. **신뢰된 IMU/GNSS 입력**: 노이즈 파라미터를 알려진 값으로 고정, GT와 대조.
4. 단계적으로 노이즈·현실성 추가.

## 통과 기준
- [ ] 완벽 특징 조건에서 ATE가 이론 하한 수준
- [ ] 현실 노이즈에서 목표 정확도 달성 (지표 TBD)
- [ ] replay 회귀 테스트 통과 (결정론)
- [ ] 다양한 궤적에서 발산 없음

## 산출물
- `estimator_bringup/` (구독·평가 런치)
- `eval/` (ATE/RPE 스크립트, 리포트)
- 회귀용 rosbag 세트
