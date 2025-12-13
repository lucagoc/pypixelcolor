from ..lib.transport.send_plan import single_window_plan

def show_slot(number: int):
    """
    Shows the specified slot on the device.

    Args:
        number: The slot number to display.
        
    Note:
        If the slot is empty, the device will cycle through available slots.
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
