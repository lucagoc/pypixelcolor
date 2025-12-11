from ..lib.transport.send_plan import single_window_plan

def show_slot(number: int):
    """
    Shows the specified slot on the device.

    Args:
        number: The slot number to display.
    """
    cmd = bytes([
        0x07,
        0x00,
        0x08,
        0x80,
        0x01,
        0x00,
        int(number) & 0xFF,
    ])
    return single_window_plan("show_slot", cmd)
