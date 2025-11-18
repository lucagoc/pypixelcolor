from ..lib.transport.send_plan import single_window_plan

def set_brightness(level: int):
    """
    Set the brightness of the device.
    
    Args:
        level (int): Brightness level (0-100).
    """
    if (0 > int(level)) or (int(level) > 100):
        raise ValueError("Brightness level must be between 0 and 100")
    payload = bytes([
        5,          # Command length
        0,          # Reserved
        4,          # Command ID
        0x80,       # Command type ID
        int(level)  # Brightness value
    ])
    return single_window_plan("set_brightness", payload)
