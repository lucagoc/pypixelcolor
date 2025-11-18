from . import (
    clear,
    delete,
    set_brightness,
    set_clock_mode,
    set_rhythm_mode,
    set_fun_mode,
    set_time,
    set_orientation,
    set_power,
    send_text,
    send_image
)

COMMANDS = {
    "clear": clear.clear,
    "set_brightness": set_brightness.set_brightness,
    "set_clock_mode": set_clock_mode.set_clock_mode,
    "set_rhythm_mode": set_rhythm_mode.set_rhythm_mode,
    "set_rhythm_mode_2": set_rhythm_mode.set_rhythm_mode_2,
    "set_time": set_time.set_time,
    "set_fun_mode": set_fun_mode.set_fun_mode,
    "set_pixel": set_fun_mode.set_pixel,
    "delete": delete.delete,
    "send_text": send_text.send_text,
    "set_orientation": set_orientation.set_orientation,
    "send_image": send_image.send_image,
    "set_power": set_power.set_power,
}

# 0x80  -> ?
# 1     -> ?
COMMANDS_ID = {
    (1, 0x80): set_time.set_time,
    (3, 0x80): clear.clear,
    (4, 0x80): set_brightness.set_brightness,
    (6, 0x80): set_orientation.set_orientation,
    # ---
    (2, 1): delete.delete,
    (4, 1): set_fun_mode.set_fun_mode,
    (5, 1): set_fun_mode.set_pixel,
    (6, 1): set_clock_mode.set_clock_mode,
    (7, 1): set_power.set_power,
    # ---
    (0, 2): set_rhythm_mode.set_rhythm_mode_2,
    (1, 2): set_rhythm_mode.set_rhythm_mode,
}