# Hands-On: Docker setup

Instructor-facing notes. The **student walkthrough** lives in
[`README.md`](README.md).

## Layout

```
ROS2-ASCI-RTS/
├── docker-compose.yml        # two profiles: "hello" and "sim"
├── docker/
│   ├── Dockerfile            # ros:humble + f1tenth_gym + bridge + wall_follower
│   └── entrypoint.sh
├── config/
│   └── sim.yaml              # F1TENTH sim config (Levine map, teleop off)
└── wall_follower/            # the editable Python node (mounted live)
    └── wall_follower/wall_follow.py
```

## Distribution: local build on each machine

There is no hosted image. Every machine builds `ros2-handson:latest` locally
from `docker/Dockerfile`. The build pulls the `ros:humble` base from Docker Hub
and clones `f1tenth_gym` + `f1tenth_gym_ros` from GitHub, so each machine needs
**internet at build time** (~5 min).

```bash
docker compose --profile sim build
```

> Have students run this **before** the session, not during it. If the room's
> network is unreliable, the fallback is to build once and ship a tarball
> (`docker save ros2-handson:latest | gzip > ros2-handson.tar.gz`, then
> `docker load < ros2-handson.tar.gz` on each machine), but the default plan is
> a local build per machine.

## Quick smoke test

```bash
# Stage 1
docker compose --profile hello up        # expect talker/listener chatter
docker compose --profile hello down

# Stage 2 (needs a display)
xhost +local:docker
docker compose --profile sim up          # RViz opens, car follows the wall
```

## Notes

- `network_mode: host` + a shared `ROS_DOMAIN_ID=42` give automatic node
  discovery with zero DDS config.
- The wall follower runs via `python3 …/wall_follow.py` against a **live mount**,
  so a `docker compose restart wall_follower` picks up edits with no rebuild.
- RViz uses software OpenGL (`LIBGL_ALWAYS_SOFTWARE=1`) so it works on CPU-only
  laptops.
- Topics: sim publishes `/scan`, subscribes `/drive`; the wall follower is the
  bridge between them and also publishes `/wallfollow/latency_ms`.
```
