from enum import IntEnum
from typing import Union

from ..lib.transport.send_plan import SendPlan, single_window_plan


class TimerAction(IntEnum):
    """Timer action: STOP (0), START (1), PAUSE (2)."""
    STOP = 0
    START = 1
    PAUSE = 2


def _parse_action(action: Union[TimerAction, str, int]) -> TimerAction:
    """Convert and validate action into a TimerAction enum."""
    if isinstance(action, TimerAction):
        return action

    if isinstance(action, str):
        cleaned = action.strip().upper()
        if cleaned in TimerAction.__members__:
            return TimerAction[cleaned]
        if cleaned.isdigit():
            action = int(cleaned)

    if isinstance(action, int) and not isinstance(action, bool):
        try:
            return TimerAction(action)
        except ValueError:
            pass

    raise ValueError(
        f"Invalid timer action: {action!r}. Expected 'start', 'pause', 'stop' (or 0, 1, 2)."
    )


def set_timer(action: Union[TimerAction, str, int]) -> SendPlan:
    """
    Set timer action (start, pause, stop).

    Args:
        action (Union[TimerAction, str, int]): TimerAction enum, string ('start', 'pause', 'stop'),
            or integer (0 = stop, 1 = start, 2 = pause).

    Returns:
        SendPlan: The single window send plan for this command.
    """
    timer_action = _parse_action(action)

    payload = bytes([
        5,                  # Command length
        0,                  # Reserved
        9,                  # Command ID
        0x80,               # Command type ID
        timer_action.value  # Value: 0 = stop, 1 = start, 2 = pause
    ])
    return single_window_plan("set_timer", payload)
