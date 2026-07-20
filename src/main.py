from __future__ import annotations
from pyray import (
    begin_drawing,
    begin_mode_3d,
    Camera3D,
    CameraMode,
    CameraProjection,
    clear_background,
    close_window,
    disable_cursor,
    draw_cylinder_ex,
    draw_model_ex,
    draw_plane,
    draw_sphere,
    draw_text,
    end_drawing,
    end_mode_3d,
    init_window,
    is_key_pressed,
    KeyboardKey,
    LIGHTGRAY,
    RAYWHITE,
    set_target_fps,
    set_trace_log_level,
    TraceLogLevel,
    update_camera,
    Vector2,
    Vector3,
    WHITE,
    window_should_close,
)
from .models import Hub, Connection, Map, ModelManager
from .parse import parse_input
from .monitor import Monitor
from .pathfinding import PathStep


_COLOR_MAP: dict[str, tuple[int, int, int, int]] = {
    "red":     (230,  41,  55, 255),
    "green":   (  0, 228,  48, 255),
    "blue":    (  0, 121, 241, 255),
    "yellow":  (253, 249,   0, 255),
    "gray":    (130, 130, 130, 255),
    "grey":    (130, 130, 130, 255),
    "orange":  (255, 161,   0, 255),
    "purple":  (200, 122, 255, 255),
    "cyan":    (  0, 247, 247, 255),
    "white":   (255, 255, 255, 255),
    "black":   ( 20,  20,  20, 255),
    "maroon":  (112,  31,  22, 255),
    "brown":   (127,  95,   0, 255),
    "gold":    (255, 203,   0, 255),
    "violet":  (135,  60, 190, 255),
    "crimson": (220,  20,  60, 255),
}

_DEFAULT_COLOR: tuple[int, int, int, int] = (0, 121, 241, 255)
_START_COLOR:   tuple[int, int, int, int] = (0, 228,  48, 255)
_END_COLOR:     tuple[int, int, int, int] = (253, 249,  0, 255)
_CONN_COLOR:    tuple[int, int, int, int] = (130, 130, 130, 255)

_PROPELLER_MESHES: tuple[int, ...] = (112, 113, 114, 115)
_PROPELLER_PIVOTS: tuple[tuple[float, float, float], ...] = (
    (0.0,    1.6406, 0.0),
    (0.0,    1.6406, 0.0),
    (-2.125, 1.6406, 0.0),
    (-2.125, 1.6406, 0.0),
)
_PROPELLER_SPEED: float = 20.0  # radians/second

_DRONE_MODEL_KEY  = "drone"
_DRONE_MODEL_PATH = "models/drone.glb"

_SCALE = 3.0

def _hub_color(hub: Hub) -> tuple[int, int, int, int]:
    """Resolve display colour for a hub."""
    if hub.is_start:
        return _START_COLOR
    if hub.is_end:
        return _END_COLOR
    if hub.color is not None:
        return _COLOR_MAP.get(hub.color.lower(), _DEFAULT_COLOR)
    return _DEFAULT_COLOR


def draw_connection(connection: Connection) -> None:
    p1 = Vector3(connection.hub1.x * _SCALE, 0.5, connection.hub1.y * _SCALE)
    p2 = Vector3(connection.hub2.x * _SCALE, 0.5, connection.hub2.y * _SCALE)
    draw_cylinder_ex(p1, p2, 0.1, 0.1, 8, _CONN_COLOR)


def draw_hub(hub: Hub) -> None:
    pos = Vector3(hub.x * _SCALE, 0.5, hub.y * _SCALE)
    draw_sphere(pos, 0.5, _hub_color(hub))


def draw_map(game_map: Map) -> None:
    for connection in game_map.connections:
        draw_connection(connection)
    for hub in game_map.hubs:
        draw_hub(hub)


def draw_drone(hub: Hub) -> None:

    model = ModelManager.get(_DRONE_MODEL_KEY)
    wx = hub.x * _SCALE
    wy = 1.5
    wz = hub.y * _SCALE

    draw_model_ex(
        model,
        Vector3(wx, wy, wz),
        Vector3(0.0, 1.0, 0.0),
        -90.0,
        Vector3(1.0, 1.0, 1.0),
        WHITE,
    )


def draw_drones_at_turn(paths: list[list[PathStep]], start_hub: Hub, current_turn: int) -> None:

    for steps in paths:
        if not steps:
            continue

        hub = start_hub
        for step_hub, step_turn in steps:
            if step_turn <= current_turn:
                hub = step_hub
            else:
                break

        draw_drone(hub)


def main() -> None:

    game_map = parse_input("map.txt")
    if game_map is None:
        return

    monitor = Monitor(game_map)
    monitor.init_drones()
    monitor.run()

    monitor.print_output()
    monitor.print_summary()

    if game_map.start_hub is None:
        return

    set_trace_log_level(TraceLogLevel.LOG_ERROR)
    init_window(1920, 1080, "Fly-in — drone router")
    ModelManager.load(_DRONE_MODEL_KEY, _DRONE_MODEL_PATH)

    camera = Camera3D(
        Vector3(10.0, 10.0, 10.0),
        Vector3(0.0,  0.0,  0.0),
        Vector3(0.0,  1.0,  0.0),
        45.0,
        CameraProjection.CAMERA_PERSPECTIVE,
    )

    disable_cursor()
    set_target_fps(60)

    current_turn: int = 0
    total_turns: int  = monitor.turn

    while not window_should_close():
        update_camera(camera, CameraMode.CAMERA_FREE)

        if is_key_pressed(KeyboardKey.KEY_RIGHT) or is_key_pressed(KeyboardKey.KEY_SPACE):
            if current_turn < total_turns:
                current_turn += 1
        if is_key_pressed(KeyboardKey.KEY_LEFT):
            if current_turn > 0:
                current_turn -= 1
        if is_key_pressed(KeyboardKey.KEY_Z):
            camera.target = Vector3(0.0, 0.0, 0.0)

        begin_drawing()
        clear_background(RAYWHITE)

        begin_mode_3d(camera)
        draw_plane(
            Vector3(0.0, 0.0, 0.0),
            Vector2(500.0, 500.0),
            LIGHTGRAY,
        )
        draw_map(game_map)
        draw_drones_at_turn(
            monitor._paths,
            game_map.start_hub,
            current_turn,
        )
        end_mode_3d()

        draw_text(
            f"Drones: {game_map.nb_drones}  "
            f"Zones: {len(game_map.hubs)}  "
            f"Connections: {len(game_map.connections)}",
            10, 10, 20, (0, 0, 0, 255),
        )
        draw_text(
            f"Turn: {current_turn} / {total_turns}",
            10, 35, 24,
            (0, 100, 0, 255) if current_turn < total_turns else (180, 0, 0, 255),
        )
        draw_text(
            "[←/→] Step turns  |  [Z] Reset camera  |  WASD + Mouse: free cam",
            10, 65, 18, (100, 100, 100, 255),
        )

        end_drawing()

    ModelManager.unload_all()
    close_window()