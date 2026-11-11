from ..lib.transport.send_plan import SendPlan, single_window_plan
from ..lib.device_info import DeviceInfo
from typing import Optional


def set_fun_mode(enable : bool = False):
    """
    Enable or disable fun mode.

    Args:
        enable: Boolean or equivalent, enables (True) or disables (False) fun mode.
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


def set_pixels(points: list[tuple[int, int]], color: str, device_info: Optional[DeviceInfo] = None) -> SendPlan:
    """
    Paint one or more pixels in a single frame.

    Painted pixels are only visible while the panel is in fun mode
    (see ``set_fun_mode``). The frame is fire-and-forget: the panel
    does not ACK paint writes.

    Args:
        points: List of (x, y) coordinates, each coordinate a single byte.
        color: Color in hexadecimal format (e.g., 'FF0000' for red).
        device_info: Device information (injected automatically by DeviceSession).
    """
    
    # Validate coordinates range if device info is provided
    for x, y in points:
        if device_info and not (0 <= int(x) <= device_info.width - 1 and 0 <= int(y) <= device_info.height - 1):
                raise ValueError(f"Invalid coordinates range. Range are x[0:{device_info.width-1}] y[0:{device_info.height-1}]")
    if not points:
            raise ValueError("At least one point is required.")
    if len(points) > 123:
            raise ValueError(f"Too many points: {len(points)}. Maximum is 123 (the frame length is a single byte).")
        
    # Validate color format
    if not (isinstance(color, str) and len(color) == 6 and all(c in '0123456789abcdefABCDEF' for c in color)):
            raise ValueError("Color must be a 6-character hexadecimal string.")
    
    # Build payload using bytes
    payload = [
        8 + 2 * len(points),      # Command length
        0,                        # Reserved
        5,                        # Command ID
        1,                        # Command type ID
        0,                        # Reserved
        int(color[0:2], 16),      # Red
        int(color[2:4], 16),      # Green
        int(color[4:6], 16),      # Blue
    ]
    for x, y in points:
        payload.append(int(x))    # X coordinate
        payload.append(int(y))    # Y coordinate

    return single_window_plan("set_pixels", bytes(payload), requires_ack=False)


def set_pixel(x: int, y: int, color: str, device_info: Optional[DeviceInfo] = None):
    """
    Defines the color of a specific pixel.

    Args:
        x: X coordinate of the pixel (0-...).
        y: Y coordinate of the pixel (0-...).
        color: Color in hexadecimal format (e.g., 'FF0000' for red).
    """
    return set_pixels([(x, y)], color, device_info=device_info)
