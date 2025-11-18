from ..lib.transport.send_plan import single_window_plan
from ..lib.device_info import DeviceInfo
from typing import Optional


def set_fun_mode(enable : bool = False):
    """
    Enable or disable fun mode.
    Args:
        enable: Boolean or equivalent, enables (True) or disables (False) fun mode.
    Returns:
        A SendPlan to enable/disable fun mode.
    """
    
    # Convert bool
    if isinstance(enable, str):
        enable = enable.lower() in ("true", "1", "yes", "on")
    
    # Build payload using bytes
    payload = bytes([
        5,                        # Command length
        0,                        # Reserved
        4,                        # Command ID
        1,                        # Command type ID
        1 if bool(enable) else 0  # Fun mode value
    ])
    
    return single_window_plan("set_fun_mode", payload)


def set_pixel(x: int, y: int, color: str, device_info: Optional[DeviceInfo] = None):
    """
    Defines the color of a specific pixel.
    Args:
        x: X coordinate of the pixel (0-...).
        y: Y coordinate of the pixel (0-...).
        color: Color in hexadecimal format (e.g., 'FF0000' for red).
    Returns:
        A SendPlan to define the color of the pixel.
    """
    
    # Validate coordinates range if device info is provided
    if device_info and not (0 <= int(x) <= device_info.width - 1 and 0 <= int(y) <= device_info.height - 1):
            raise ValueError(f"Invalid coordinates range. Range are x[0:{device_info.width-1}] y[0:{device_info.height-1}]")
        
    # Validate color format
    if (not (isinstance(color, str)) 
        and len(color) == 6 
        and all(c in '0123456789abcdefABCDEF' for c in color)):
            raise ValueError("Color must be a 6-character hexadecimal string.")
    
    # Build payload using bytes
    payload = bytes([
        10,                       # Command length
        0,                        # Reserved
        5,                        # Command ID
        1,                        # Command type ID
        0,                        # Reserved
        int(color[0:2], 16),      # Red
        int(color[2:4], 16),      # Green
        int(color[4:6], 16),      # Blue
        int(x),                   # X coordinate
        int(y)                    # Y coordinate
    ])
    
    return single_window_plan("set_pixel", payload, requires_ack=False)
