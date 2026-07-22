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
    get_frame_time,
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
from .models import ModelManager
from .parse import parse_input
from .monitor import Monitor
from .graphic import Graphic

_DRONE_MODEL_PATH = "models/drone.glb"
_DRONE_MODEL_KEY  = "drone"

def main() -> None:

    game_map = parse_input("map1.txt")
    if game_map is None:
        return

    graphic = Graphic()
    monitor = Monitor(game_map)
    monitor.init_drones()
    monitor.run()

    monitor.print_output()
    monitor.print_summary()

    if game_map.start_hub is None:
        return

    set_trace_log_level(TraceLogLevel.LOG_ERROR)
    init_window(1920, 1080, "Fly-in")
    ModelManager.load(_DRONE_MODEL_KEY, _DRONE_MODEL_PATH)

    camera = Camera3D(Vector3(10.0, 10.0, 10.0), Vector3(0.0,  0.0,  0.0), Vector3(0.0,  1.0,  0.0), 45.0, CameraProjection.CAMERA_PERSPECTIVE)

    disable_cursor()
    set_target_fps(60)

    current_turn: float = 0.0
    target_turn: int = 0
    total_turns: int = monitor.turn
    ANIM_SPEED = 2.0

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
            current_turn = min(target_turn, current_turn + ANIM_SPEED * dt)
        elif current_turn > target_turn:
            current_turn = max(target_turn, current_turn - ANIM_SPEED * dt)


        begin_drawing()
        clear_background(RAYWHITE)

        begin_mode_3d(camera)
        draw_plane(Vector3(0.0, 0.0, 0.0), Vector2(500.0, 500.0), LIGHTGRAY)
        graphic.draw_map(game_map)
        graphic.draw_drones_at_turn(monitor._paths, game_map.start_hub, current_turn)
        end_mode_3d()

        draw_text(f"Drones: {game_map.nb_drones}  " f"Zones: {len(game_map.hubs)}  " f"Connections: {len(game_map.connections)}", 10, 10, 20, (0, 0, 0, 255))
        draw_text(f"Turn: {int(current_turn)} / {total_turns}", 10, 35, 24,(0, 100, 0, 255) if current_turn < total_turns else (180, 0, 0, 255))
        draw_text("[G/F] Step turns  |  [Z] Reset camera  |  WASD + Mouse: free cam", 10, 65, 18, (100, 100, 100, 255))

        end_drawing()

    ModelManager.unload_all()
    close_window()