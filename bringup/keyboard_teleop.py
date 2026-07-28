#!/usr/bin/env python3
"""PX4 offboard 키보드 teleop (자동 이륙 + ARM 상태 표시).

실행(래퍼 권장):  bash ~/drone_ws/bringup/teleop.sh
직접 실행 시:      source ~/drone_ws/bringup/env.sh 후 python3 이 파일

키:
  T : arm + offboard + 자동 이륙(5m) ← 먼저 이거!
  W/S 전진/후진   A/D 좌/우   R/F 상승/하강   Q/E yaw(±0.2)
  Space 정지(hover)   L 착륙   +/- 속도스케일   Ctrl-C 종료
화면 하단에 [ARMED/DISARMED] 와 고도가 실시간 표시됩니다.
"""
import math, sys, select, termios, tty, threading
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy
from px4_msgs.msg import (OffboardControlMode, TrajectorySetpoint,
                          VehicleCommand, VehicleLocalPosition, VehicleStatus)

TAKEOFF_ALT = 5.0
def qos():
    return QoSProfile(reliability=ReliabilityPolicy.BEST_EFFORT,
                      durability=DurabilityPolicy.VOLATILE,
                      history=HistoryPolicy.KEEP_LAST, depth=10)

class Teleop(Node):
    def __init__(s):
        super().__init__("keyboard_teleop"); q=qos()
        s.ocm=s.create_publisher(OffboardControlMode,"/fmu/in/offboard_control_mode",q)
        s.sp=s.create_publisher(TrajectorySetpoint,"/fmu/in/trajectory_setpoint",q)
        s.cmd=s.create_publisher(VehicleCommand,"/fmu/in/vehicle_command",q)
        s.create_subscription(VehicleLocalPosition,"/fmu/out/vehicle_local_position_v1",s._lp,q)
        s.create_subscription(VehicleStatus,"/fmu/out/vehicle_status_v4",s._st,q)
        s.vx=s.vy=s.vz=s.yr=0.0; s.scale=1.5
        s.heading=0.0; s.z=0.0; s.armed=False; s.taking_off=False; s.n=0
        s.create_timer(0.05,s._tick)
    def _lp(s,m): s.heading=m.heading; s.z=m.z
    def _st(s,m): s.armed=(m.arming_state==2)
    def _cmd(s,c,p1=0.0,p2=0.0):
        m=VehicleCommand(); m.timestamp=int(s.get_clock().now().nanoseconds/1000)
        m.command=c; m.param1=p1; m.param2=p2; m.target_system=1; m.target_component=1
        m.source_system=1; m.source_component=1; m.from_external=True; s.cmd.publish(m)
    def _tick(s):
        s.n+=1
        o=OffboardControlMode(); o.timestamp=int(s.get_clock().now().nanoseconds/1000)
        o.velocity=True; s.ocm.publish(o)
        alt=-s.z
        # 자동 이륙 로직
        if s.taking_off:
            if alt < TAKEOFF_ALT-0.3: s.vz=1.5
            else: s.vz=0.0; s.taking_off=False; s.get_logger().info(f"이륙완료 {alt:.1f}m — WASD로 조종")
        c,sn=math.cos(s.heading),math.sin(s.heading)
        sp=TrajectorySetpoint(); sp.timestamp=int(s.get_clock().now().nanoseconds/1000)
        sp.position=[float('nan')]*3
        sp.velocity=[s.vx*c-s.vy*sn, s.vx*sn+s.vy*c, -s.vz]
        sp.acceleration=[float('nan')]*3; sp.jerk=[float('nan')]*3
        sp.yaw=float('nan'); sp.yawspeed=s.yr; s.sp.publish(sp)
    def start(s):
        # arm 전 셋포인트 스트림 확보 위해 잠깐 대기 후 arm
        s._cmd(VehicleCommand.VEHICLE_CMD_DO_SET_MODE,1.0,6.0)
        s._cmd(VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM,1.0)
        s.taking_off=True; s.get_logger().info("ARM+OFFBOARD 전송 → 자동 이륙 5m")
    def land(s):
        s._cmd(VehicleCommand.VEHICLE_CMD_NAV_LAND); s.vx=s.vy=s.vz=s.yr=0.0; s.taking_off=False
    def key(s,k):
        v=s.scale
        if k=="t": s.start()
        elif k=="l": s.land()
        elif k=="w": s.vx=v
        elif k=="s": s.vx=-v
        elif k=="a": s.vy=-v
        elif k=="d": s.vy=v
        elif k=="r": s.vz=v
        elif k=="f": s.vz=-v
        elif k=="q": s.yr=max(-2.0,s.yr-0.2)
        elif k=="e": s.yr=min(2.0,s.yr+0.2)
        elif k==" ": s.vx=s.vy=s.vz=s.yr=0.0
        elif k=="+": s.scale=min(5.0,s.scale+0.5)
        elif k=="-": s.scale=max(0.5,s.scale-0.5)

def key_loop(n):
    print(__doc__)
    fd=sys.stdin.fileno(); old=termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        while rclpy.ok():
            if select.select([sys.stdin],[],[],0.1)[0]:
                k=sys.stdin.read(1)
                if k=="\x03": break
                n.key(k.lower())
            st="ARMED " if n.armed else "DISARM"
            sys.stdout.write(f"\r[{st}] alt={-n.z:+.1f}m v=({n.vx:+.1f},{n.vy:+.1f},{n.vz:+.1f}) yaw={n.yr:+.1f} scale={n.scale:.1f}   ")
            sys.stdout.flush()
    finally:
        termios.tcsetattr(fd,termios.TCSADRAIN,old)

def main():
    rclpy.init(); n=Teleop()
    threading.Thread(target=rclpy.spin,args=(n,),daemon=True).start()
    try: key_loop(n)
    except KeyboardInterrupt: pass
    finally: rclpy.shutdown()

if __name__=="__main__": main()
