from ..lib.transport.send_plan import single_window_plan

def clear():
    """
    Clears the EEPROM.
    """
    cmd = bytes([
        4,     # Command length
        0,     # Reserved
        3,     # Command ID
        0x80,  # Command type ID
    ])
    return single_window_plan("clear", cmd)
