"""arm+offboard 후 target 고도까지 상승 후 유지 (고도별 캡처용)."""
import sys, rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy
from px4_msgs.msg import OffboardControlMode, TrajectorySetpoint, VehicleCommand, VehicleLocalPosition
TARGET=float(sys.argv[1]) if len(sys.argv)>1 else 45.0
def qos(): return QoSProfile(reliability=ReliabilityPolicy.BEST_EFFORT,durability=DurabilityPolicy.VOLATILE,history=HistoryPolicy.KEEP_LAST,depth=10)
class C(Node):
    def __init__(s):
        super().__init__("climb_hold"); q=qos()
        s.ocm=s.create_publisher(OffboardControlMode,"/fmu/in/offboard_control_mode",q)
        s.sp=s.create_publisher(TrajectorySetpoint,"/fmu/in/trajectory_setpoint",q)
        s.cmd=s.create_publisher(VehicleCommand,"/fmu/in/vehicle_command",q)
        s.create_subscription(VehicleLocalPosition,"/fmu/out/vehicle_local_position_v1",s.lp,q)
        s.z=0.0; s.t=0; s.create_timer(0.05,s.tick)
    def lp(s,m): s.z=m.z
    def send(s,c,p1=0.0,p2=0.0):
        m=VehicleCommand(); m.timestamp=int(s.get_clock().now().nanoseconds/1000); m.command=c; m.param1=p1; m.param2=p2
        m.target_system=1; m.target_component=1; m.source_system=1; m.source_component=1; m.from_external=True; s.cmd.publish(m)
    def tick(s):
        s.t+=1
        o=OffboardControlMode(); o.timestamp=int(s.get_clock().now().nanoseconds/1000); o.velocity=True; s.ocm.publish(o)
        alt=-s.z; err=TARGET-alt; vz=max(-3.0,min(3.0,err*0.5))
        sp=TrajectorySetpoint(); sp.timestamp=int(s.get_clock().now().nanoseconds/1000)
        sp.position=[float('nan')]*3; sp.velocity=[0.0,0.0,-vz]; sp.acceleration=[float('nan')]*3; sp.jerk=[float('nan')]*3
        sp.yaw=float('nan'); sp.yawspeed=0.0; s.sp.publish(sp)
        if s.t==20: s.send(VehicleCommand.VEHICLE_CMD_DO_SET_MODE,1.0,6.0); s.send(VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM,1.0)
        if s.t%20==0: s.get_logger().info(f"alt={alt:.1f}m")
rclpy.init(); n=C()
try: rclpy.spin(n)
except (KeyboardInterrupt,SystemExit): pass
rclpy.shutdown()
