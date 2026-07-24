# Phase 3 — Guarded Takeover (추정값 기반 제어)

## 목표
자작 estimator를 **제어의 상태원(state source)** 으로 삼아 폐루프 비행.
안전장치(guard)와 fallback을 갖춘 점진적 이양.

## 제어 주입 방식 (명시적 선택 필요)
`vehicle_visual_odometry`는 **EKF2가 융합만 하지 대체하지 않음**. "내 추정값으로 제어"하려면:

- **(A) EKF2 비활성 + uORB 직접 발행**: EKF2를 끄고 estimator가 컨트롤러가 소비하는
  `vehicle_odometry` / `vehicle_local_position` / `vehicle_attitude` uORB를 직접 채움.
  → estimator = 유일 상태원. uORB 계약 구현 필요.
- **(B) 외부 컨트롤러**: PX4 제어 밖에서 자작 컨트롤러가 estimator 출력을 소비.
  → 제어까지 완전 자작.

기본 채택: **(A)** (PX4 제어 재사용, 상태원만 교체). 필요 시 (B).

## Guard / Fallback
- estimator health monitor (covariance 폭주, 지연 초과, NaN 감지).
- 이상 시 EKF2로 **자동 복귀** 또는 안전 모드(hover/land).
- 소프트 스타트: hover→저속→기동 순 점진 확대.

## 통과 기준
- [ ] hover 폐루프 안정 (estimator 상태원)
- [ ] 기본 궤적(사각/8자) 추종 오차 목표 내
- [ ] guard 트리거 → fallback 정상 동작
- [ ] EKF2 제어 대비 성능 비교표

## 산출물
- uORB 발행 브리지 (또는 외부 컨트롤러)
- health monitor + fallback 로직
- 폐루프 성능 리포트
