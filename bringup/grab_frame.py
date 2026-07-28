import sys, time, numpy as np, rclpy
from rclpy.node import Node
from rclpy.qos import QoSPresetProfiles
from sensor_msgs.msg import Image
from PIL import Image as PImage

class Grab(Node):
    def __init__(self, out):
        super().__init__("grab"); self.out=out; self.done=False
        self.create_subscription(Image, (sys.argv[2] if len(sys.argv)>2 else "/airsim_node/Drone1/front_center_Scene/image"),
                                 self.cb, QoSPresetProfiles.SENSOR_DATA.value)
    def cb(self, m):
        if self.done: return
        a = np.frombuffer(bytes(m.data), dtype=np.uint8)
        ch = a.size // (m.height*m.width)
        a = a.reshape(m.height, m.width, ch)
        if ch == 4: a = a[:, :, :3]
        if m.encoding.startswith("bgr"): a = a[:, :, ::-1]
        PImage.fromarray(a, "RGB").save(self.out)
        self.done = True; self.get_logger().info(f"saved {self.out} {a.shape}")

rclpy.init(); n=Grab(sys.argv[1]); t0=time.time()
while rclpy.ok() and not n.done and time.time()-t0<10: rclpy.spin_once(n, timeout_sec=0.5)
rclpy.shutdown()
