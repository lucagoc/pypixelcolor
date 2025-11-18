from ..lib.transport.send_plan import single_window_plan

def set_power(on: bool = True):
    """
    Set the power state of the device.
    Args:
        on: True to turn on, False to turn off.
    Returns:
        A SendPlan to set the power state.
    """
    if isinstance(on, str):
        on = on.lower() in ("true", "1", "yes", "on")
    
    # Build command
    cmd = bytes([
        5,              # Command length
        0,              # Reserved
        7,              # Command ID
        1,              # Command type ID
        1 if on else 0  # Power state
    ])
    return single_window_plan("set_power", cmd)
