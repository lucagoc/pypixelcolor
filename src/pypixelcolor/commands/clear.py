from ..lib.transport.send_plan import single_window_plan

def clear():
    """
    Clears the ROM data on the device.
    
    Note:
        This command removes all stored content from the device's memory, including device settings.
    """
    cmd = bytes([
        4,     # Command length
        0,     # Reserved
        3,     # Command ID
        0x80,  # Command type ID
    ])
    return single_window_plan("clear", cmd)
