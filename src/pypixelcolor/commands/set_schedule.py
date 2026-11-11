# -*- coding: utf-8 -*-
"""Command to set on/off schedule by time and day of week."""

from enum import IntFlag
from typing import Union

from ..lib.transport.send_plan import SendPlan, single_window_plan


class ScheduleDay(IntFlag):
    """Days of the week bitmask for schedule."""
    MON = 0x02
    TUE = 0x04
    WED = 0x08
    THU = 0x10
    FRI = 0x20
    SUN = 0x40
    SAT = 0x80


_DAYS = {
    "mon": ScheduleDay.MON,
    "tue": ScheduleDay.TUE,
    "wed": ScheduleDay.WED,
    "thu": ScheduleDay.THU,
    "fri": ScheduleDay.FRI,
    "sat": ScheduleDay.SAT,
    "sun": ScheduleDay.SUN,
}


def _parse_days(days: Union[ScheduleDay, int, str, list[str], None]) -> int:
    """Parse days mask (defaults to all days, bit 0 set to 1)."""
    if days is None:
        return 0xFF

    if isinstance(days, (ScheduleDay, int)):
        mask = int(days)
        if not (0 <= mask <= 255):
            raise ValueError(f"Days mask must be between 0 and 255 (got {mask})")
        return mask | 1

    if isinstance(days, str):
        days = days.split(",")

    mask = 1
    for d in days:
        key = d.strip().lower()
        if key not in _DAYS:
            raise ValueError(f"Unknown day: {d!r}. Expected: {list(_DAYS.keys())}")
        mask |= _DAYS[key]

    return mask


def set_schedule(
    hour: int,
    minute: int,
    on: bool,
    days: Union[ScheduleDay, int, str, list[str], None] = None,
    slot: int = 0,
) -> SendPlan:
    """
    Set an automated on/off schedule by time and day of week.

    Args:
        hour (int): Hour (0-23). Defaults to 12.
        minute (int): Minute (0-59). Defaults to 0.
        on (bool): True to turn display ON, False to turn OFF. Defaults to True.
        days (Union[ScheduleDay, int, str, list[str], None]): Active days ('mon,sat' or ['mon', 'sat']). Defaults to all days.
        slot (int): Schedule slot index (0, 1, 2, ...). Defaults to 0.

    Returns:
        SendPlan: The single window send plan for this command.
    """
    if isinstance(on, str):
        on = on.lower() in ("true", "1", "yes", "on")

    hour = int(hour)
    minute = int(minute)
    slot = int(slot)

    if not (0 <= hour <= 23):
        raise ValueError(f"Hour must be between 0 and 23 (got {hour})")
    if not (0 <= minute <= 59):
        raise ValueError(f"Minute must be between 0 and 59 (got {minute})")
    if not (0 <= slot <= 255):
        raise ValueError(f"Slot must be between 0 and 255 (got {slot})")

    days_mask = _parse_days(days)

    payload = bytes([
        9,                  # Command length
        0,                  # Reserved
        0x11,               # Command ID (17)
        0x80,               # Command type ID
        1 if on else 0,     # Action: 1 = on, 0 = off
        slot,               # Slot index
        days_mask,          # Days bitmask
        hour,               # Hour
        minute,             # Minute
    ])

    return single_window_plan("set_schedule", payload)
