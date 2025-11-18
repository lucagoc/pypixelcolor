from ..lib.transport.send_plan import single_window_plan

def set_rhythm_mode(style=0, l1 : int = 0, l2 : int = 0, l3 : int = 0, l4 : int = 0, l5 : int = 0, l6 : int = 0, l7 : int = 0, l8 : int = 0, l9 : int = 0, l10 : int = 0, l11 : int = 0):
    """Set the rhythm mode of the device.

    Args:
        style (int): The style of the rhythm mode (0-4).
        l1 (int): Level 1 (0-15).
        l2 (int): Level 2 (0-15).
        l3 (int): Level 3 (0-15).
        l4 (int): Level 4 (0-15).
        l5 (int): Level 5 (0-15).
        l6 (int): Level 6 (0-15).
        l7 (int): Level 7 (0-15).
        l8 (int): Level 8 (0-15).
        l9 (int): Level 9 (0-15).
        l10 (int): Level 10 (0-15).
        l11 (int): Level 11 (0-15).

    Returns:
        bytes: Byte sequence for the command payload used to set the rhythm mode.

    Raises:
        ValueError: If ``style`` is not in 0..4 or any level is not in 0..15.
    """

    # Validation
    if not (0 <= int(style) <= 4):
        raise ValueError(f"rhythm mode style must be between 0 and 4, got {style}")

    levels = [int(v) for v in [l1, l2, l3, l4, l5, l6, l7, l8, l9, l10, l11]]
    for idx, lv in enumerate(levels, start=1):
        if not (0 <= lv <= 15):
            raise ValueError(f"level {idx} must be between 0 and 15, got {lv}")

    # Build payload
    payload = bytes([
        16,     # Command length
        0,      # Reserved
        1,      # Command ID
        2,      # Command type ID
        int(style),
    ])
    payload += bytes(levels)
    
    return single_window_plan("set_rhythm_mode", payload, requires_ack=True)


def set_rhythm_mode_2(style: int = 0, t: int = 0):
    """Set the rhythm mode of the device (alternative version).

    Args:
        style (int): The style of the rhythm mode. Allowed values are 0 or 1.
        t (int): Animation time (0-7).

    Returns:
        bytes: Byte sequence for the command payload used to set the rhythm mode.

    Raises:
        ValueError: If ``style`` is not in 0..1 or ``t`` is not in 0..7.
    """
    
    # Validation
    if not (0 <= int(style) <= 1):
        raise ValueError(f"rhythm mode style must be between 0 and 1, got {style}")
    
    if not (0 <= int(t) <= 7):
        raise ValueError(f"Level (t) must be between 0 and 7, got {t}")

    # Build payload using bytes
    payload = bytes([
        6,              # Command length
        0,              # Reserved
        0,              # Command ID
        2,              # Command type ID
        int(t),         # Animation time
        int(style)      # Style
    ])
    
    return single_window_plan("set_rhythm_mode_2", payload)
