"""Entry point: parse a map, run the simulation, then visualize it.

Usage:
    python3 -m src [map_path] [--no-gui]

If ``map_path`` is omitted, a small demo map is used. ``--no-gui``
skips the 3D window and only prints the turn-by-turn simulation
output, which is useful for headless environments and quick checks.
"""

import argparse
import sys

from pyray import (
    Camera3D,
    CameraMode,
    CameraProjection,
    KeyboardKey,
    LIGHTGRAY,
    RAYWHITE,
    TraceLogLevel,
    Vector2,
    Vector3,
    begin_drawing,
    begin_mode_3d,
    clear_background,
    close_window,
    disable_cursor,
    draw_plane,
    draw_text,
    end_drawing,
    end_mode_3d,
    get_frame_time,
    init_window,
    is_key_pressed,
    set_target_fps,
    set_trace_log_level,
    update_camera,
    window_should_close,
)

from .graphic import Graphic
from .models import Map, ModelManager
from .monitor import Monitor
from .parse import Parser

_DRONE_MODEL_PATH = "models/drone.glb"
_DRONE_MODEL_KEY = "drone"
_DEFAULT_MAP_PATH = "maps/easy/01_linear_path.txt"
_ANIM_SPEED = 2.0


def parse_args(argv: list[str]) -> argparse.Namespace:
    """
    Parse command-line arguments.

    Args:
        argv: Raw argument list (excluding the program name).

    Returns:
        Namespace with ``map_path`` and ``no_gui`` attributes.
    """
    parser = argparse.ArgumentParser(
        prog="fly-in",
        description="Route a fleet of drones across a zone graph.",
    )
    parser.add_argument(
        "map_path",
        nargs="?",
        default=_DEFAULT_MAP_PATH,
        help=f"path to the map input file (default: {_DEFAULT_MAP_PATH})",
    )
    parser.add_argument(
        "--no-gui",
        action="store_true",
        help="only print the simulation output, skip the 3D window",
    )
    return parser.parse_args(argv)


def _run_gui(game_map: Map, monitor: Monitor, graphic: Graphic) -> None:
    """
    Open the 3D window and animate the already-computed simulation.

    All raylib resources are released in a ``finally`` block so that
    a failure while loading the model or during the render loop
    never leaves the window or the loaded model behind.

    Args:
        game_map: The map to draw.
        monitor: Monitor holding the drones' reserved paths.
        graphic: Renderer used to draw hubs, connections and drones.
    """
    if game_map.start_hub is None:
        return

    total_turns: int = monitor.turn
    current_turn: float = 0.0
    target_turn: int = 0

    set_trace_log_level(TraceLogLevel.LOG_ERROR)
    init_window(1920, 1080, "Fly-in")

    try:
        ModelManager.load(_DRONE_MODEL_KEY, _DRONE_MODEL_PATH)

        camera = Camera3D(
            Vector3(10.0, 10.0, 10.0),
            Vector3(0.0, 0.0, 0.0),
            Vector3(0.0, 1.0, 0.0),
            45.0,
            CameraProjection.CAMERA_PERSPECTIVE,
        )

        disable_cursor()
        set_target_fps(60)

        while not window_should_close():
            update_camera(camera, CameraMode.CAMERA_FREE)

            if is_key_pressed(KeyboardKey.KEY_G) and target_turn < total_turns:
                target_turn += 1
            if is_key_pressed(KeyboardKey.KEY_F) and target_turn > 0:
                target_turn -= 1
            if is_key_pressed(KeyboardKey.KEY_Z):
                camera.target = Vector3(0.0, 0.0, 0.0)

            dt = get_frame_time()
            if current_turn < target_turn:
                current_turn = min(
                    target_turn, current_turn + _ANIM_SPEED * dt
                )
            elif current_turn > target_turn:
                current_turn = max(
                    target_turn, current_turn - _ANIM_SPEED * dt
                )

            begin_drawing()
            clear_background(RAYWHITE)

            begin_mode_3d(camera)
            draw_plane(
                Vector3(0.0, 0.0, 0.0), Vector2(500.0, 500.0), LIGHTGRAY
            )
            graphic.draw_map(game_map)
            graphic.draw_drones_at_turn(
                monitor._paths, game_map.start_hub, current_turn
            )
            end_mode_3d()

            draw_text(
                f"Drones: {game_map.nb_drones}  "
                f"Zones: {len(game_map.hubs)}  "
                f"Connections: {len(game_map.connections)}",
                10, 10, 20, (0, 0, 0, 255),
            )
            draw_text(
                f"Turn: {int(current_turn)} / {total_turns}",
                10, 35, 24,
                (0, 100, 0, 255)
                if current_turn < total_turns
                else (180, 0, 0, 255),
            )
            draw_text(
                "[G/F] Step turns  |  [Z] Reset camera  |  "
                "WASD + Mouse: free cam",
                10, 65, 18, (100, 100, 100, 255),
            )

            end_drawing()
    finally:
        ModelManager.unload_all()
        close_window()


def main() -> None:
    """Parse the requested map, simulate it, then optionally show it."""
    args = parse_args(sys.argv[1:])

    parser = Parser()
    game_map = parser.parse_input(args.map_path)
    if game_map is None:
        sys.exit(1)

    monitor = Monitor(game_map)
    monitor.init_drones()
    monitor.run()

    monitor.print_output()
    monitor.print_summary()

    if args.no_gui:
        return

    _run_gui(game_map, monitor, Graphic())
