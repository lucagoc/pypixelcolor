from ..lib.transport.send_plan import SendPlan, single_window_plan
from ..lib.device_info import DeviceInfo
from enum import IntEnum
from typing import Optional, Union


class MirrorMode(IntEnum):
    """Paint mirror modes understood by the panel."""
    NONE = 0
    HORIZONTAL = 1
    VERTICAL = 2


def _parse_mirror(mirror: Union[MirrorMode, str, int, None]) -> MirrorMode:
    """Convert and validate a mirror mode into a MirrorMode enum."""
    if mirror is None:
        return MirrorMode.NONE

    if isinstance(mirror, MirrorMode):
        return mirror

    if isinstance(mirror, str):
        cleaned = mirror.strip().upper().replace("-", "_")
        if cleaned in MirrorMode.__members__:
            return MirrorMode[cleaned]
        if cleaned.isdigit():
            mirror = int(cleaned)

    if isinstance(mirror, int) and not isinstance(mirror, bool):
        try:
            return MirrorMode(mirror)
        except ValueError:
            pass

    valid_names = ", ".join(m.lower() for m in MirrorMode.__members__)
    raise ValueError(
        f"Invalid mirror mode: {mirror!r}. Expected {valid_names} (or 0, 1, 2)."
    )


def set_fun_mode(enable: bool = False):
    """
    Enable or disable the DIY (fun) display mode.

    The panel's DIY canvas is a live layer: painted pixels (protocol type 5)
    are only visible while the panel is in DIY mode. Entering DIY mode shows
    the canvas and, on exit, the panel restores whatever was displayed before
    entry. This command switches between the two states.

    The full mode byte (``[len,5,0,4,1,<mode>]``) has four values; this
    command exposes the two the panel actually needs:

    * ``enable=True``  -> mode ``1`` (ENTER_CLEAR_CUR_SHOW): enter DIY mode
      and clear the canvas.
    * ``enable=False`` -> mode ``0`` (QUIT_NOSAVE_KEEP_PREV): exit DIY mode,
      discard the canvas, and restore the previous show.

    (Mode ``3`` ENTER_NO_CLEAR_CUR_SHOW also enters without clearing; mode
    ``2`` QUIT_STILL_CUR_SHOW is unused.)

    This write is fire-and-forget: the panel does not ACK it (like type-5
    paint frames), so no ACK is awaited.

    Args:
        enable: Boolean or equivalent, enables (True) or disables (False)
            fun mode.
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

    # Fire-and-forget: verified on hardware that the panel never ACKs this
    # write; waiting 8 s for an ACK would always time out.
    return single_window_plan("set_fun_mode", payload, requires_ack=False)


def set_pixels(points: list[tuple[int, int]], color: str, device_info: Optional[DeviceInfo] = None, mirror: Union[MirrorMode, str, int, None] = None) -> SendPlan:
    """
    Paint one or more pixels in a single frame.

    Painted pixels are only visible while the panel is in fun mode
    (see ``set_fun_mode``). The frame is fire-and-forget: the panel
    does not ACK paint writes.

    Args:
        points: List of (x, y) coordinates, each coordinate a single byte.
        color: Color in hexadecimal format (e.g., 'FF0000' for red).
        device_info: Device information (injected automatically by DeviceSession).
        mirror: Optional mirror mode ('horizontal' or 'vertical', or a
            MirrorMode value). The panel then paints every point plus its
            mirror image on the opposite side, in the same color.
    """
    
    mirror_mode = _parse_mirror(mirror)
    
    # Validate coordinates range if device info is provided
    for x, y in points:
        if device_info and not (0 <= int(x) <= device_info.width - 1 and 0 <= int(y) <= device_info.height - 1):
            raise ValueError(f"Invalid coordinates range. Range are x[0:{device_info.width-1}] y[0:{device_info.height-1}]")
    if not points:
        raise ValueError("At least one point is required.")
    if len(points) > 123:
        raise ValueError(f"Too many points: {len(points)}. Maximum is 123 (the frame length is a single byte).")
        
    # Validate color format
    if not (
        isinstance(color, str)
        and len(color) == 6
        and all(c in '0123456789abcdefABCDEF' for c in color)
    ):
        raise ValueError("Color must be a 6-character hexadecimal string.")
    
    # Build payload using bytes
    payload = [
        8 + 2 * len(points),      # Command length
        0,                        # Reserved
        5,                        # Command ID
        1,                        # Command type ID
        int(mirror_mode),         # Mirror / move type
        int(color[0:2], 16),      # Red
        int(color[2:4], 16),      # Green
        int(color[4:6], 16),      # Blue
    ]
    for x, y in points:
        payload.append(int(x))    # X coordinate
        payload.append(int(y))    # Y coordinate

    return single_window_plan("set_pixels", bytes(payload), requires_ack=False)


def set_pixel(x: int, y: int, color: str, device_info: Optional[DeviceInfo] = None, mirror: Union[MirrorMode, str, int, None] = None):
    """
    Defines the color of a specific pixel.

    Args:
        x: X coordinate of the pixel (0-...).
        y: Y coordinate of the pixel (0-...).
        color: Color in hexadecimal format (e.g., 'FF0000' for red).
        mirror: Optional mirror mode, see ``set_pixels``.
    """
    return set_pixels([(x, y)], color, device_info=device_info, mirror=mirror)
