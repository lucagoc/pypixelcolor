# Imports
from datetime import datetime

# Locals
from ..lib.transport.send_plan import single_window_plan

# Commands
def set_clock_mode(style: int = 1, date="", show_date: bool = True, format_24: bool = True):
    """
    Set the clock mode of the device.

    Args:
        style (int, optional): The clock style (0-8). Defaults to 1.
        date (str, optional): The date to display (DD/MM/YYYY). Defaults to today.
        show_date (bool, optional): Whether to show the date. Defaults to True.
        format_24 (bool, optional): Whether to use 24-hour format. Defaults to True.

    Returns:
        bytes: Encoded command to send to the device.
    """
    if isinstance(show_date, str):
        show_date = show_date.lower() in ("true", "1", "yes", "on")
    if isinstance(format_24, str):
        format_24 = format_24.lower() in ("true", "1", "yes", "on")

    # Process date
    if not date:
        now = datetime.now()
        day, month, year = now.day, now.month, now.year % 100
        day_of_week = now.weekday() + 1
    else:
        try:
            day, month, year = map(int, date.split("/"))
            day_of_week = datetime(year, month, day).weekday() + 1
        except (ValueError, IndexError) as e:
            raise ValueError(f"Invalid date format: {e}")

    # Validate ranges
    if int(style) not in range(0, 9):
        raise ValueError("Clock style must be between 0 and 8")
    if int(day_of_week) not in range(1, 8):
        raise ValueError("Day of week must be between 1 and 7")
    if int(year) not in range(0, 100):
        raise ValueError("Year must be between 0 and 99")
    if int(month) not in range(1, 13):
        raise ValueError("Month must be between 1 and 12")
    if int(day) not in range(1, 32):
        raise ValueError("Day must be between 1 and 31")

    # Build byte sequence using direct bytes constructions
    header = bytes([
        11, # Command length 
        0,  # Reserved
        6,  # Command ID
        1   # Command type ID
    ])

    params = bytes([
        int(style) & 0xFF,                # Clock style
        1 if bool(format_24) else 0,      # 24-hour format
        1 if bool(show_date) else 0,      # Show date
    ])

    date_bytes = bytes([
        year & 0xFF,                   # Year
        month & 0xFF,                  # Month
        day & 0xFF,                    # Day
        day_of_week & 0xFF,            # Day of week
    ])

    payload = header + params + date_bytes
    return single_window_plan("set_clock_mode", payload)
