# ROS 2 Hands-On

In the next ~30 minutes you will:

1. **Stage 1, Hello ROS 2:** run nodes yourself and look inside a running ROS 2
   system.
2. **Stage 2, Wall following:** run an F1TENTH simulator and a separate
   controller node that drives the car, and tune it live.

---

## Setup

```bash
# Build the image once. This downloads the ROS 2 base image and clones the
# F1TENTH simulator from GitHub, so you need internet for this step.
# >>> Do this BEFORE the session if you can -- it takes ~5 min. <<<
docker compose --profile sim build
```

You need Docker + Docker Compose. Stage 2 opens **RViz** and **rqt** windows, so
on Linux allow containers to use your display **once per login**:

```bash
xhost +local:docker
```

---

## Stage 1: Hello ROS 2  (~8 min)

Open an interactive shell in a container:

```bash
docker compose run --rm shell
```

### `ros2 run`: start one node

Inside the shell, start a talker:

```bash
ros2 run demo_nodes_cpp talker
```

It publishes `Hello World: N`. Open a **second terminal**, get another shell
(`docker compose run --rm shell`), and start a listener:

```bash
ros2 run demo_nodes_cpp listener
```

The listener prints what the talker publishes. `ros2 run` starts **one node
from one package**.

Now, in a **third** shell, look inside the running system:

```bash
ros2 node list                 # which nodes are running?
ros2 topic list                # which topics exist?
ros2 topic echo /chatter       # watch the messages live
ros2 topic hz /chatter         # how fast are they published?
ros2 topic info /chatter       # who publishes / subscribes?
```

### `ros2 launch`: start several nodes at once

Stop the talker and listener (`Ctrl-C` in each). `ros2 run` started one node at
a time; `ros2 launch` starts a whole set described in a launch file:

```bash
ros2 launch demo_nodes_cpp talker_listener.launch.py
```

This brings up the talker **and** the listener together from a single command.
Check with `ros2 node list` in another shell: both are running.

**The difference:** `ros2 run <pkg> <executable>` runs a single node;
`ros2 launch <pkg> <launch_file>` runs a configured group of nodes. Real
systems are started with launch files.

Exit the shells (`Ctrl-C`, then `exit`) when done.

---

## Stage 2: Wall Following in the F1TENTH Simulator  (~22 min)

We start the simulator and the controller **separately**, so you can see they
are two independent ROS 2 programs talking over topics.

### 1. Start the simulator

```bash
xhost +local:docker            # if you didn't already
docker compose --profile sim up
```

An **RViz** window opens showing the track. The car model and LiDAR scan appear
a few seconds later, once the simulator finishes starting up, give it a moment.
The car does **not** move yet: nothing is publishing drive commands.

### 2. Start the controller

In a **second terminal**:

```bash
docker compose run --rm wall_follower
```

This runs the `wall_follow` node (`ros2 run wall_follower wall_follow`). It
reads the LiDAR (`/scan`) and publishes drive commands (`/drive`), and the car
starts following the wall. Stop this node (`Ctrl-C`) and the car stops; start it
again and the car drives again.

### 3. Tune the controller live with rqt_reconfigure

In a **third terminal**, open the parameter GUI:

```bash
docker compose run --rm wall_follower ros2 run rqt_reconfigure rqt_reconfigure
```

Select the `wall_follow` node. You can change parameters with sliders **while
the car drives**, no restart needed:

| Parameter | Try | What to look for |
|---|---|---|
| `kp` | `0.4`, then `2.5` | Too low drifts into the wall; too high wobbles. |
| `kd` | raise to `0.5` | Damps the wobble from a high `kp`. |
| `desired_distance` | `0.4`, then `1.5` | The car hugs / avoids the wall. |
| `max_velocity` | raise to `7.0` | Faster laps, until it can't make a corner. |
| `follow_left_wall` | toggle | The car switches to the other wall. |

**Goal:** get a clean, fast lap without scraping the wall.

> The defaults live at the top of
> `wall_follower/wall_follower/wall_follow.py`. The source is mounted
> live, so editing the file and re-running the node also works.

### Watch the latency

With the controller from step 2 still running, it measures how long its
`scan -> drive` callback takes and publishes it. In another shell:

```bash
docker compose run --rm shell
ros2 topic echo /wallfollow/latency_ms     # processing time per scan, in ms
ros2 topic hz /drive                       # control rate
```

This is the **end-to-end latency** from the lecture, measured on a live system.

> If you see `topic does not appear to be published yet`, the controller is not
> running, the `/wallfollow/latency_ms` and `/drive` topics only exist while the
> `wall_follow` node from step 2 is alive. Start it first.

### Reset the car

If the car crashes: in RViz click **`2D Pose Estimate`** and click on the track
to drop the car back onto it.

When finished:

```bash
docker compose --profile sim down
```

---

## Extras (if you finish early)

1. **Speed from steering, not error.** Speed currently drops only when the
   *error* is large. Change `pid_control` so the car slows in proportion to how
   hard it is steering:
   ```python
   velocity = self.p('max_velocity') * (1.0 - abs(angle) / MAX_STEERING_ANGLE)
   velocity = max(self.p('min_velocity'), velocity)
   ```
   Does it corner more smoothly? Can you raise `max_velocity` higher?

2. **More robust wall estimate.** The estimate uses just two LiDAR beams.
   Average a small *window* of beams around each angle in `get_range` to reduce
   noise.

---

## Cheat sheet

```bash
# Stage 1
docker compose run --rm shell                 # interactive shell
ros2 run demo_nodes_cpp talker                # one node
ros2 launch demo_nodes_cpp talker_listener.launch.py   # a set of nodes

# Stage 2
xhost +local:docker
docker compose --profile sim up               # simulator + RViz
docker compose run --rm wall_follower         # controller
docker compose run --rm wall_follower ros2 run rqt_reconfigure rqt_reconfigure   # live tuning
docker compose --profile sim down

# Inspect a running system
ros2 node list / topic list / topic echo <topic> / topic hz <topic>
```
