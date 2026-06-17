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
    update_camera,
    Vector2,
    Vector3,
    window_should_close,
)
from .models import Hub, Connection, Map
from .parse import parse_input

_COLOR_MAP: dict[str, tuple[int, int, int, int]] = {
    "red":     (230,  41,  55, 255),
    "green":   ( 0, 228,  48, 255),
    "blue":    (  0, 121, 241, 255),
    "yellow":  (253, 249,   0, 255),
    "gray":    (130, 130, 130, 255),
    "grey":    (130, 130, 130, 255),
    "orange":  (255, 161,   0, 255),
    "purple":  (200, 122, 255, 255),
    "cyan":    (  0, 247, 247, 255),
    "white":   (255, 255, 255, 255),
    "black":   ( 0,   0,   0, 255),
}

_DEFAULT_HUB_COLOR:  tuple[int, int, int, int] = (0, 121, 241, 255)   # blue
_START_HUB_COLOR:    tuple[int, int, int, int] = (0, 228,  48, 255)   # green
_END_HUB_COLOR:      tuple[int, int, int, int] = (253, 249,  0, 255)  # yellow
_CONNECTION_COLOR:   tuple[int, int, int, int] = (130, 130, 130, 255) # gray


def _hub_color(hub: Hub) -> tuple[int, int, int, int]:
    if hub.is_start:
        return _START_HUB_COLOR
    if hub.is_end:
        return _END_HUB_COLOR
    if hub.color is not None:
        return _COLOR_MAP.get(hub.color.lower(), _DEFAULT_HUB_COLOR)
    return _DEFAULT_HUB_COLOR


def draw_connection(connection: Connection) -> None:

    p1 = Vector3(connection.hub1.x * 3.0, 0.5, connection.hub1.y * 3.0)
    p2 = Vector3(connection.hub2.x * 3.0, 0.5, connection.hub2.y * 3.0)
    draw_cylinder_ex(p1, p2, 0.1, 0.1, 8, _CONNECTION_COLOR)


def draw_hub(hub: Hub) -> None:

    pos = Vector3(hub.x * 3.0, 0.5, hub.y * 3.0)
    draw_sphere(pos, 0.5, _hub_color(hub))


def draw_map(game_map: Map) -> None:

    for connection in game_map.connections:
        draw_connection(connection)

    for hub in game_map.hubs:
        draw_hub(hub)


def main() -> None:
    
    game_map = parse_input("map.txt")
    
    if game_map is None:
        return

    screen_width = 1920
    screen_height = 1080

    init_window(screen_width, screen_height, "Fly-in — drone router")

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

        if is_key_pressed(KeyboardKey.KEY_Z):
            camera.target = Vector3(0.0, 0.0, 0.0)

        begin_drawing()
        clear_background(RAYWHITE)

        begin_mode_3d(camera)
        draw_plane(Vector3(0.0, 0.0, 0.0), Vector2(500.0, 500.0), LIGHTGRAY)
        draw_map(game_map)
        end_mode_3d()

        draw_text(
            f"Drones: {game_map.nb_drones}  "
            f"Zones: {len(game_map.hubs)}  "
            f"Connections: {len(game_map.connections)}",
            10, 10, 20, (0, 0, 0, 255)
        )
        draw_text(
            "[Z] Reset camera  |  WASD + Mouse: free cam",
            10, 35, 18, (100, 100, 100, 255)
        )

        end_drawing()

    close_window()