# =============================================================================
#  ROS 2 Hands-On image  --  F1TENTH simulator + editable wall follower
# =============================================================================
#  One image is used for everything:
#    * Stage 1 (hello world): talker / listener (built into ROS 2)
#    * Stage 2 (wall following): f1tenth_gym + f1tenth_gym_ros bridge + RViz
#                                + our wall_follower package
#
#  Built on ROS 2 Humble (Ubuntu 22.04). CPU-only. RViz via X11.
# =============================================================================
FROM ros:humble-ros-base

SHELL ["/bin/bash", "-c"]
ENV DEBIAN_FRONTEND=noninteractive

# --- System + ROS dependencies -------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
        git \
        python3-pip \
        nano \
        ros-humble-rviz2 \
        ros-humble-ackermann-msgs \
        ros-humble-tf-transformations \
        ros-humble-xacro \
        ros-humble-nav2-map-server \
        ros-humble-nav2-lifecycle-manager \
        ros-humble-joint-state-publisher \
        ros-humble-robot-state-publisher \
        ros-humble-demo-nodes-cpp \
        ros-humble-rqt-reconfigure \
    && rm -rf /var/lib/apt/lists/*

# --- f1tenth_gym (the physics simulator, a pip package) ------------------------
RUN pip3 install --no-cache-dir transforms3d \
    && git clone https://github.com/f1tenth/f1tenth_gym.git /opt/f1tenth_gym \
    && cd /opt/f1tenth_gym \
    && pip3 install --no-cache-dir -e .

# --- ROS 2 workspace -----------------------------------------------------------
ENV SIM_WS=/sim_ws
RUN mkdir -p $SIM_WS/src

# f1tenth_gym_ros bridge (the ROS 2 wrapper around the gym)
RUN git clone https://github.com/f1tenth/f1tenth_gym_ros.git $SIM_WS/src/f1tenth_gym_ros

# Our editable wall follower and the hello-world demo are mounted at runtime
# (see docker-compose.yml volumes), but we copy them once so the image also
# works standalone.
COPY wall_follower $SIM_WS/src/wall_follower

# --- Build the workspace -------------------------------------------------------
RUN source /opt/ros/humble/setup.bash \
    && cd $SIM_WS \
    && rosdep update \
    && rosdep install --from-paths src --ignore-src -r -y || true \
    && colcon build --symlink-install

# --- Entry: source ROS + workspace on every shell ------------------------------
RUN echo "source /opt/ros/humble/setup.bash" >> /root/.bashrc \
    && echo "source $SIM_WS/install/setup.bash" >> /root/.bashrc

COPY docker/safety_watchdog.py /opt/safety_watchdog.py

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]
