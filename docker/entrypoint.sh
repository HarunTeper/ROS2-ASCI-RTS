#!/bin/bash
# Source ROS 2 and the workspace, then run whatever command was given.
set -e
source /opt/ros/humble/setup.bash
if [ -f /sim_ws/install/setup.bash ]; then
    source /sim_ws/install/setup.bash
fi
exec "$@"
