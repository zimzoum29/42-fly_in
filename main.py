from pyray import *

init_window(1920, 1020, "Hello")
while not window_should_close():
    begin_drawing()
    clear_background(WHITE)
    draw_text("Hello world", 960, 540, 20, VIOLET)
    end_drawing()
close_window()