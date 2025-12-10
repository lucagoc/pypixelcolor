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
    send_image,
    show_slot
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
    "send_image_hex": send_image.send_image_hex,
    "set_power": set_power.set_power,
    "show_slot": show_slot.show_slot,
}
