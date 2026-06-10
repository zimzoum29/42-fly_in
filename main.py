from pyray import *

screen_width = 1500
screen_height = 900

init_window(screen_width, screen_height, "raylib [core] example - 3d camera free")

camera = Camera3D(
    Vector3(10.0, 10.0, 10.0),
    Vector3(0.0, 0.0, 0.0),
    Vector3(0.0, 1.0, 0.0),
    45.0,
    CameraProjection.CAMERA_PERSPECTIVE
)

cube_position = Vector3(0.0, 1.0, 0.0)

disable_cursor()
set_target_fps(60)

while not window_should_close():
    update_camera(camera, CameraMode.CAMERA_FREE)

    if is_key_pressed(KeyboardKey.KEY_Z):
        camera.target = Vector3(0.0, 0.0, 0.0)

    begin_drawing()

    clear_background(RAYWHITE)

    begin_mode_3d(camera)

    draw_cube(cube_position, 2.0, 2.0, 2.0, RED)
    draw_cube_wires(cube_position, 2.0, 2.0, 2.0, MAROON)

    draw_grid(10, 1)

    end_mode_3d()

    draw_rectangle(10, 10, 320, 93, fade(SKYBLUE, 0.5))
    draw_rectangle_lines(10, 10, 320, 93, BLUE)

    draw_text("Free camera default controls:", 20, 20, 10, BLACK)
    draw_text("- Mouse Wheel to Zoom in-out", 40, 40, 10, DARKGRAY)
    draw_text("- Mouse Wheel Pressed to Pan", 40, 60, 10, DARKGRAY)
    draw_text("- Z to zoom to (0, 0, 0)", 40, 80, 10, DARKGRAY)

    end_drawing()

close_window()