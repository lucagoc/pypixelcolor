# Imports
from datetime import datetime
from typing import Optional

# Locals
from ..lib.transport.send_plan import single_window_plan

def set_time(hour: Optional[int] = None, minute: Optional[int] = None, second: Optional[int] = None):
    """
    Set the device time.
    Note : Command is the same as get_device_info.
    
    Args:
        hour: Hour to set (0-23). If None, uses current hour.
        minute: Minute to set (0-59). If None, uses current minute.
        second: Second to set (0-59). If None, uses current second.
    
    Returns:
        A SendPlan to set the device time.
    """
    # Get current time if any component is None
    if hour is None or minute is None or second is None:
        now = datetime.now()
        hour = now.hour if hour is None else hour
        minute = now.minute if minute is None else minute
        second = now.second if second is None else second
        
    # Validate
    if not (0 <= int(hour) <= 23):
        raise ValueError("Hour must be between 0 and 23")
    if not (0 <= int(minute) <= 59):
        raise ValueError("Minute must be between 0 and 59")
    if not (0 <= int(second) <= 59):
        raise ValueError("Second must be between 0 and 59")
    
    # Build command
    cmd = bytes([
        8,              # Command length
        0,              # Reserved
        1,              # Command ID
        0x80,           # Command type ID
        int(hour),      # Hour
        int(minute),    # Minute
        int(second),    # Second
        0               # Reserved
    ])
    return single_window_plan("set_time", cmd)
