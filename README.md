*This project has been created as part of the 42 curriculum by tigondra.*

# Fly-in

## Description

Fly-in is a turn-based simulation that routes a fleet of drones from
a start zone to an end zone across a graph of connected zones
("hubs"). The map (zones, connections, zone types, capacities) is
described in a simple text format and parsed from scratch, with no
graph library involved.

The goal is to move every drone from the start to the end zone in
the fewest possible simulation turns while respecting:

- **Zone occupancy limits** (`max_drones`), with the start and end
  zones exempt from any limit.
- **Connection capacity limits** (`max_link_capacity`).
- **Zone-type movement costs**: `normal`/`priority` cost 1 turn,
  `restricted` costs 2 turns (and cannot be interrupted mid-transit),
  `blocked` zones can never be entered.

Each drone is routed with a turn-aware pathfinding search, and every
computed path is "reserved" (hub occupancy per turn, connection
occupancy per turn) before the next drone is routed, so later drones
automatically avoid conflicting with earlier ones.

The simulation output (one line per turn, `D<id>-<zone>` /
`D<id>-<connection>` per moving drone) is printed to the terminal,
and the whole run is additionally replayed as an animated 3D scene.

## Instructions

Requirements: Python 3.10+, [uv](https://docs.astral.sh/uv/).

```sh
make install   # installs dependencies (raylib/pyray) via uv
make run       # parses and simulates maps/easy/01_linear_path.txt,
               # prints the turn-by-turn output, then opens the 3D view
```

Run a different map by passing it through `ARGS`:

```sh
make run ARGS="maps/hard/02_capacity_hell.txt"
```

Skip the 3D window and only print the simulation output (useful on
a machine without a display):

```sh
make run ARGS="--no-gui"
make run ARGS="maps/hard/02_capacity_hell.txt --no-gui"
```

Or call the module directly, the same way `make run` does under the
hood:

```sh
uv run python3 -m src maps/medium/03_priority_puzzle.txt --no-gui
```

Other targets: `make debug` (runs under `pdb`, also accepts `ARGS`),
`make lint` (flake8 + mypy with the flags required by the subject),
`make lint-strict` (flake8 + `mypy --strict`), `make clean`.

Once the 3D window is open: `WASD` + mouse to move the free camera,
`G`/`F` to step forward/backward one simulation turn, `Z` to reset
the camera.

## Algorithm choices and implementation strategy

- **Sequential, reservation-based routing.** Drones are routed one
  at a time (`Monitor.init_drones`), each through
  `PathFinder.find_path`. Every accepted path is immediately
  committed via `PathFinder.register_path` into two shared tables:
  `reservation` (how many drones occupy a given hub at a given turn)
  and `link_reservation` (how many drones traverse a given
  connection at a given turn). The next drone's search sees — and
  avoids — every conflict already reserved by previous drones. This
  keeps the search itself a simple, well-understood single-agent
  algorithm while still producing a conflict-free multi-drone
  schedule.
- **State space and complexity.** The search explores
  `(hub, turn)` states with a binary heap (`heapq`), i.e. a
  Dijkstra/A*-style search over time-expanded states — roughly
  `O(E · T log(V · T))` per drone in the worst case, where `V`/`E`
  are the map's hubs/connections and `T` is the turn budget
  (capped at 200 turns via `_MAX_TURNS` to guarantee termination on
  unsolvable instances).
- **Tie-breaking.** Among equally-short paths, a lexicographic key
  `(detour_penalty, congestion_score, -priority_bonus)` picks the
  one that backtracks the least, avoids already-crowded hubs/links,
  and passes through `priority` zones when possible — matching the
  subject's requirement that priority zones "should be prioritized
  in pathfinding" even though they don't cost less than `normal`.
- **Restricted-zone transit.** A 2-turn move into a `restricted`
  zone is treated as a single atomic edge in the search (no waiting
  mid-transit is possible, matching the subject), but its connection
  is reserved for **both** turns of the transit, not just the
  departure turn — otherwise a second drone could start using the
  same connection while the first one is still on it.
- **No graph library.** `Map`/`Hub`/`Connection` in `models.py` are
  a minimal, hand-rolled adjacency-list graph, as required by the
  subject's constraints.
- **Caching.** Nothing is recomputed: each drone's path is computed
  once and stored (`Monitor._paths`), then reused both to print the
  turn-by-turn text output and to drive the 3D animation.

## Visual representation

The project uses a **graphical interface** (a real-time 3D scene
built with [raylib](https://www.raylib.com/) via its Python bindings,
`pyray`): hubs are colored spheres (color taken from the map file's
`color` metadata, or a default for the start/end zones), connections
are cylinders between hubs, and each drone is a 3D model smoothly
interpolated along its reserved path. Turns can be stepped forward
and backward (`G`/`F`) to inspect the schedule, which makes capacity
conflicts, waiting drones and restricted-zone transits easy to
follow visually instead of only reading the raw text output.

A `--no-gui` flag is also available to print only the textual,
turn-by-turn output (see Instructions), for headless use.

## Resources

- Dijkstra Algorithm on the [wikipedia page](https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm)
- [raylib](https://www.raylib.com/) / [pyray (Python
  bindings)](https://electronstudio.github.io/raylib-python-cffi/)
  documentation, for the 3D rendering layer.
- Python [`typing`](https://docs.python.org/3/library/typing.html)
  and [`heapq`](https://docs.python.org/3/library/heapq.html)
  standard library documentation.
- General background reading on time-expanded graphs for
  multi-agent pathfinding with capacity constraints (the same idea
  behind this project's `(hub, turn)` state space).
- **AI usage**: an AI assistant was used to help for the docstrings and flake8 errors. Also that help me to understand some notion about the project.
