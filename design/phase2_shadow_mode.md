# Phase 2 — Shadow Mode (EKF2 비행 중 병렬 비교)

## 목표
**제어권은 여전히 PX4 EKF2**가 쥔 채로, 자작 estimator를 **실시간 병렬(shadow)** 로 돌려
비행 중 조건에서의 정확도·지연·robustness를 게이트로 검증. (codex 권고: 제어 이양 전 필수 단계)

## 왜 필요한가
open-loop(Phase 1)는 정확도를 보지만 실시간·폐루프 동특성은 못 봄.
estimator 버그를 제어 불안정으로 오진하는 것을 막기 위해, 실제 비행 동역학 하에서
**추정값만 그림자로** 평가한다.

## 접근
- EKF2가 비행(제어), estimator는 동일 센서 스트림을 실시간 구독해 `/estimator/odom` 발행.
- 3자 비교: estimator vs EKF2 출력 vs GT.
- **Fault injection**: 센서 드롭아웃, 지연 스파이크, GNSS 음영, 노이즈 급증 주입 후 estimator 거동 관찰.

## 통과 기준 (Gate — 제어 이양 전제조건)
- [ ] 실시간성: estimator 지연이 제어 주기 대비 허용 범위
- [ ] 정확도: 비행 중 ATE/RPE 목표 달성
- [ ] Reset/재초기화: 트리거 후 정상 복귀
- [ ] Fault injection 하에서 발산·폭주 없음, 열화 후 회복
- [ ] covariance가 실제 오차와 일관 (consistency, NEES/NIS)

## 산출물
- shadow 실행 런치 (EKF2 + estimator 동시)
- fault injection 도구
- 3자 비교 + consistency 리포트
