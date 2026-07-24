# 01. Sim Adapter 계약 (Conformance Contract)

시뮬레이터를 estimator 검증에 쓸 때 **최대 위험은 센서 아티팩트가 estimator 오차로 둔갑**하는 것.
adapter는 단순 브리지가 아니라 **정식 timing/frame 계약 + conformance test**여야 한다.
이 계약을 지키면 estimator/제어 모듈은 sim(AirSim↔Gazebo↔JSBSim)이 바뀌어도 **무수정 이식**된다.

## 표준 인터페이스 (ROS2 토픽)

| 목적 | 토픽(예) | 메시지 타입 | 출처 |
|---|---|---|---|
| IMU | `/drone/imu` | `sensor_msgs/Imu` | PX4/JSBSim (AirSim pose 미분 금지) |
| GNSS | `/drone/gnss` | `sensor_msgs/NavSatFix` | PX4/JSBSim |
| 카메라 | `/drone/cam/image` | `sensor_msgs/Image`(+`CameraInfo`) | AirSim (photorealistic) |
| Ground truth | `/drone/gt/pose` | `geometry_msgs/PoseStamped` | sim GT |
| estimator 출력 | `/estimator/odom` | `nav_msgs/Odometry` | 자작 estimator |
| 제어 상태원(폐루프) | uORB `vehicle_odometry` 등 | (PX4 내부) | estimator→PX4 |

## 계약 항목 (conformance test 대상)

1. **Clock authority / sim-time**
   - `/clock` 단일 권위. 모든 노드 `use_sim_time=true`.
   - AirSim: SteppableClock, PX4 lockstep 활성.

2. **Deterministic lockstep stepping**
   - PX4 ↔ sim 물리 lockstep. 같은 입력 → 같은 궤적(반복성).
   - 검증: 동일 시나리오 2회 실행 → GT 궤적 bit/근사 동일.

3. **Timestamp origin**
   - 센서 스탬프가 **실제 노출/샘플 시점**을 가리킴. 측정 지연 명시.
   - 검증: IMU 스탬프 단조 증가, dt 지터 한계 내.

4. **TF / frame 규약 + ENU↔NED 변환** ⚠️ **버그 최다 지점**
   - AirSim = **NED**, ROS = **ENU**. body축 규약 명문화(FRD vs FLU).
   - IMU/GNSS/카메라 extrinsic(TF) 정의.
   - 검증: 알려진 기동(정지 hover, +X 이동)에서 부호/축 일치.

5. **Latency 모델**
   - 센서→토픽 지연 재현·측정.

6. **Covariance**
   - 노이즈 모델 파라미터 ↔ 메시지 covariance 필드 일관.

7. **Reset semantics**
   - 에피소드 리셋 시 시계·상태 정합. estimator 재초기화 규약.

## Conformance Test 체크리스트
- [ ] `/clock` 단조 증가, 모든 노드 sim-time 사용
- [ ] lockstep 반복성 (2회 실행 궤적 일치)
- [ ] IMU dt 지터 < 임계
- [ ] hover 시 IMU accel ≈ (0,0,±g) 부호 정확 (NED/ENU 확인)
- [ ] +X/+Y/+Z 이동 시 GNSS·GT·estimator 부호 일치
- [ ] 카메라 스탬프 ↔ IMU 스탬프 정렬 (동기)
- [ ] covariance 필드 채워짐
- [ ] reset 후 시계·상태 재초기화 정상
