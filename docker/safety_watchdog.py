#!/usr/bin/env python3
# =============================================================================
#  Safety watchdog (runs inside the simulator container).
#
#  The F1TENTH gym holds the last /drive command forever, so a controller that
#  dies (crash, hard kill) would leave the car driving. This node watches
#  /drive and, if no fresh command has arrived recently, publishes a zero-speed
#  stop command. While a controller is alive (publishing at LiDAR rate) the
#  watchdog stays silent and never interferes.
# =============================================================================

import rclpy
from rclpy.node import Node
from ackermann_msgs.msg import AckermannDriveStamped

TIMEOUT_S = 0.3          # consider the controller dead after this much silence
CHECK_PERIOD_S = 0.05    # how often we check


class SafetyWatchdog(Node):
    def __init__(self):
        super().__init__('safety_watchdog')
        self.last_cmd_time = None
        self.stopped = False

        # Subscribe and publish on the SAME topic the controller uses.
        self.sub = self.create_subscription(
            AckermannDriveStamped, '/drive', self.on_drive, 10)
        self.pub = self.create_publisher(AckermannDriveStamped, '/drive', 10)
        self.timer = self.create_timer(CHECK_PERIOD_S, self.on_timer)

        self.get_logger().info('Safety watchdog active on /drive.')

    def on_drive(self, msg):
        # Ignore our own stop messages (speed 0) so we do not refresh on them.
        if msg.drive.speed == 0.0:
            return
        self.last_cmd_time = self.get_clock().now()
        self.stopped = False

    def on_timer(self):
        if self.last_cmd_time is None:
            return  # no controller has ever published; sim holds the car still
        age = (self.get_clock().now() - self.last_cmd_time).nanoseconds * 1e-9
        if age > TIMEOUT_S and not self.stopped:
            stop = AckermannDriveStamped()
            stop.header.stamp = self.get_clock().now().to_msg()
            stop.drive.speed = 0.0
            stop.drive.steering_angle = 0.0
            self.pub.publish(stop)
            self.stopped = True
            self.get_logger().warn(
                'No /drive command for %.2fs -> stopping the car.' % age)


def main(args=None):
    rclpy.init(args=args)
    node = SafetyWatchdog()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
