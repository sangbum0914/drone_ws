"""스크립트 비행 데모: offboard 로 이륙→상승→전진→선회→hover. 사용자가 창에서 관찰."""
import math, rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy
from px4_msgs.msg import OffboardControlMode, TrajectorySetpoint, VehicleCommand, VehicleLocalPosition

def qos():
    return QoSProfile(reliability=ReliabilityPolicy.BEST_EFFORT, durability=DurabilityPolicy.VOLATILE,
                      history=HistoryPolicy.KEEP_LAST, depth=10)

class Fly(Node):
    def __init__(self):
        super().__init__("fly_demo"); q=qos()
        self.ocm=self.create_publisher(OffboardControlMode,"/fmu/in/offboard_control_mode",q)
        self.sp=self.create_publisher(TrajectorySetpoint,"/fmu/in/trajectory_setpoint",q)
        self.cmd=self.create_publisher(VehicleCommand,"/fmu/in/vehicle_command",q)
        self.create_subscription(VehicleLocalPosition,"/fmu/out/vehicle_local_position_v1",self.lp,q)
        self.z=0.0; self.heading=0.0; self.t=0; self.armed=False
        self.vx=self.vy=self.vz=self.yr=0.0
        self.create_timer(0.05,self.tick)
    def lp(self,m): self.z=m.z; self.heading=m.heading
    def send(self,c,p1=0.0,p2=0.0):
        m=VehicleCommand(); m.timestamp=int(self.get_clock().now().nanoseconds/1000)
        m.command=c; m.param1=p1; m.param2=p2; m.target_system=1; m.target_component=1
        m.source_system=1; m.source_component=1; m.from_external=True; self.cmd.publish(m)
    def tick(self):
        self.t+=1
        o=OffboardControlMode(); o.timestamp=int(self.get_clock().now().nanoseconds/1000)
        o.velocity=True; self.ocm.publish(o)
        c,s=math.cos(self.heading),math.sin(self.heading)
        sp=TrajectorySetpoint(); sp.timestamp=int(self.get_clock().now().nanoseconds/1000)
        sp.position=[float('nan')]*3
        sp.velocity=[self.vx*c-self.vy*s, self.vx*s+self.vy*c, -self.vz]
        sp.acceleration=[float('nan')]*3; sp.jerk=[float('nan')]*3
        sp.yaw=float('nan'); sp.yawspeed=self.yr; self.sp.publish(sp)
        # 시퀀스 (0.05s tick)
        if self.t==20: self.send(VehicleCommand.VEHICLE_CMD_DO_SET_MODE,1.0,6.0); self.send(VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM,1.0); self.get_logger().info("ARM+OFFBOARD")
        elif 40<=self.t<160: self.vz=3.0   # 6초 상승 (~18m)
        elif 160<=self.t<180: self.vz=0.0
        elif 180<=self.t<340: self.vx=4.0; self.vz=0.0   # 8초 전진 (~32m, 도시 통과)
        elif 340<=self.t<440: self.vx=0.0; self.yr=0.5   # 선회
        elif 440<=self.t<520: self.vx=0.0; self.yr=0.0   # hover
        if self.t%20==0: self.get_logger().info(f"t={self.t/20:.0f}s alt={-self.z:+.1f}m v=({self.vx},{self.vy},{self.vz})")
        if self.t>=520:
            self.send(VehicleCommand.VEHICLE_CMD_NAV_LAND); self.get_logger().info("LAND"); raise SystemExit
rclpy.init(); n=Fly()
try: rclpy.spin(n)
except (SystemExit,KeyboardInterrupt): pass
rclpy.shutdown()
