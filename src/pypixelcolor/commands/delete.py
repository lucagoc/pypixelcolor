from ..lib.transport.send_plan import single_window_plan


def delete(n: int):
    """
    Delete a specific screen by its index.
    Args:
        n: Index of the screen to delete.
    Returns:
        A SendPlan to delete the specified screen.
    """
    if not (0 <= int(n) <= 255):
        raise ValueError("Screen index must be between 0 and 255")
    cmd = bytes([
        7,      # Command length
        0,      # Reserved
        2,      # Command ID
        1,      # Command type ID
        1,      # Reserved
        0,      # Reserved
        int(n)  # Screen index
    ])
    return single_window_plan("delete_screen", cmd)
