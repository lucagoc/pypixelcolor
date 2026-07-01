# Imports
from datetime import datetime

# Locals
from ..lib.transport.send_plan import single_window_plan

# Commands
def set_clock_mode(style: int = 1, date="", show_date: bool = True, format_24: bool = True, color: str = "ffffff", intensity: int = 100):
    """
    Set the clock mode of the device.
    Time is set automatically during connection via Bluetooth.

    Args:
        style (int, optional): The clock style (0-9). Defaults to 1.
            - 0-8: Built-in clock styles
            - 9: Custom digital style with black background
        date (str, optional): The date to display (DD/MM/YYYY). Defaults to today.
        show_date (bool, optional): Whether to show the date. Defaults to True.
        format_24 (bool, optional): Whether to use 24-hour format. Defaults to True.
        color (str, optional): Font color in hex format (e.g., "ff0000" for red). Only for style 9. Defaults to "ffffff" (white).
        intensity (int, optional): Font brightness/intensity (0-100). Only for style 9. Defaults to 100.

    Raises:
        ValueError: If any parameter is out of range or invalid.
    """
    if isinstance(show_date, str):
        show_date = show_date.lower() in ("true", "1", "yes", "on")
    if isinstance(format_24, str):
        format_24 = format_24.lower() in ("true", "1", "yes", "on")

    # Validate color format for style 9
    if int(style) == 9:
        try:
            color_bytes = bytes.fromhex(color)
            if len(color_bytes) != 3:
                raise ValueError("Color must be 3 bytes (6 hex chars), e.g. 'ffffff'")
        except Exception as e:
            raise ValueError(f"Invalid color hex: {color}. Use format like 'ff0000' for red.")
        
        intensity = int(intensity)
        if intensity < 0 or intensity > 100:
            raise ValueError("Intensity must be between 0 and 100")

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
    if int(style) not in range(0, 10):
        raise ValueError("Clock style must be between 0 and 9")
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

    # For style 9, append color and intensity bytes
    if int(style) == 9:
        color_bytes = bytes.fromhex(color)
        # Scale intensity from 0-100 to 0-255
        intensity_byte = int((intensity / 100) * 255)
        style_params = bytes([
            intensity_byte & 0xFF,      # Font intensity (0-255)
            color_bytes[0],             # Red channel
            color_bytes[1],             # Green channel
            color_bytes[2],             # Blue channel
            0,                          # Background color red (0 for black)
            0,                          # Background color green (0 for black)
            0,                          # Background color blue (0 for black)
        ])
        payload = header + params + date_bytes + style_params
    else:
        payload = header + params + date_bytes

    return single_window_plan("set_clock_mode", payload)