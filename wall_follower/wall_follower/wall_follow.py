#!/usr/bin/env python3
# =============================================================================
#  Wall follower for the F1TENTH simulator.
#
#  Subscribes to the LiDAR (/scan) and publishes a drive command (/drive).
#  The control loop is a PID wall-follower (the F1TENTH "wall follow" lab),
#  ported from the C++ node on our RoboRacer car.
#
#  All gains are ROS 2 parameters, so they can be tuned live with
#  rqt_reconfigure while the node runs. The values below are only the defaults.
# =============================================================================

import math
import time

import rclpy
from rclpy.node import Node

from sensor_msgs.msg import LaserScan
from ackermann_msgs.msg import AckermannDriveStamped
from std_msgs.msg import Float64


# Two LiDAR beams used to estimate the wall angle (radians from straight ahead)
SCAN_ANGLE_A = math.radians(40.0)   # the more-forward beam
SCAN_ANGLE_B = math.radians(90.0)   # the side beam (perpendicular to the car)

MAX_STEERING_ANGLE = 0.435          # [rad] physical steering limit (~25 deg)


class WallFollow(Node):
    def __init__(self):
        super().__init__('wall_follow')

        # --- Tunable parameters (live-adjustable via rqt_reconfigure) --------
        self.declare_parameter('kp', 1.0)                # proportional gain
        self.declare_parameter('kd', 0.10)               # derivative gain
        self.declare_parameter('ki', 0.0)                # integral gain
        self.declare_parameter('desired_distance', 0.8)  # [m] target wall dist
        self.declare_parameter('max_velocity', 4.0)      # [m/s] on straights
        self.declare_parameter('min_velocity', 1.5)      # [m/s] in corners
        self.declare_parameter('lookahead_distance', 1.0)  # [m] projection
        self.declare_parameter('follow_left_wall', True)

        self.prev_error = 0.0
        self.integral = 0.0
        self.scan_count = 0

        self.scan_sub = self.create_subscription(
            LaserScan, '/scan', self.scan_callback, 10)
        self.drive_pub = self.create_publisher(
            AckermannDriveStamped, '/drive', 10)
        self.latency_pub = self.create_publisher(
            Float64, '/wallfollow/latency_ms', 10)

        self.get_logger().info('WallFollow started. Tune parameters with rqt_reconfigure.')

    # --- Convenience accessors for the current parameter values -------------
    def p(self, name):
        return self.get_parameter(name).value

    # --- Read one LiDAR beam at a given angle, return distance in meters. ---
    def get_range(self, scan, angle):
        if angle < scan.angle_min or angle > scan.angle_max:
            return -1.0
        index = int(round((angle - scan.angle_min) / scan.angle_increment))
        if index < 0 or index >= len(scan.ranges):
            return -1.0
        dist = scan.ranges[index]
        if math.isnan(dist) or math.isinf(dist):
            return -1.0
        return float(dist)

    # --- Estimate how far we are from the desired wall distance. ---
    def get_error(self, scan, desired_dist):
        follow_left = self.p('follow_left_wall')
        angle_a = SCAN_ANGLE_A if follow_left else -SCAN_ANGLE_A
        angle_b = SCAN_ANGLE_B if follow_left else -SCAN_ANGLE_B

        range_a = self.get_range(scan, angle_a)
        range_b = self.get_range(scan, angle_b)
        if range_a < 0.0 or range_b < 0.0:
            return 0.0

        # Law of cosines: angle of the wall relative to the car heading.
        swing = angle_b - angle_a
        alpha = math.atan2(range_a * math.cos(swing) - range_b,
                           range_a * math.sin(swing))

        # Current distance to the wall, projected a bit ahead.
        current_distance = range_b * math.cos(alpha)
        projected = current_distance + self.p('lookahead_distance') * math.sin(alpha)
        return desired_dist - projected

    # --- PID -> steering angle + speed, then publish the drive command. ---
    def pid_control(self, error):
        derivative = error - self.prev_error
        self.integral += error
        angle = (self.p('kp') * error
                 + self.p('kd') * derivative
                 + self.p('ki') * self.integral)
        self.prev_error = error

        # Clamp steering to the physical limit.
        angle = max(-MAX_STEERING_ANGLE, min(MAX_STEERING_ANGLE, angle))

        # Slow down when the error is large (i.e. in corners).
        velocity = self.p('min_velocity') if abs(error) > 1.0 else self.p('max_velocity')

        self.publish_drive(float(velocity), float(-angle))

    def publish_drive(self, speed, steering_angle):
        msg = AckermannDriveStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.drive.speed = speed
        msg.drive.steering_angle = steering_angle
        self.drive_pub.publish(msg)

    def stop(self):
        # Publish a zero-speed command so the car does not coast on the last
        # command when this node stops.
        self.publish_drive(0.0, 0.0)

    def scan_callback(self, scan_msg):
        t_start = time.perf_counter()

        error = self.get_error(scan_msg, self.p('desired_distance'))
        self.pid_control(error)

        elapsed_ms = (time.perf_counter() - t_start) * 1000.0
        self.latency_pub.publish(Float64(data=elapsed_ms))
        self.scan_count += 1
        if self.scan_count % 100 == 0:
            self.get_logger().info(
                f'scan->drive latency: {elapsed_ms:.3f} ms   '
                f'(error={error:+.2f} m)')


def main(args=None):
    rclpy.init(args=args)
    node = WallFollow()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        # Stop the car before shutting down so it does not keep driving.
        node.stop()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
