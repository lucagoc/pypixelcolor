from ..lib.transport.send_plan import single_window_plan
from .send_text import send_text


def text_speed(text: str, speed: int = 80, char_height: int = 16, **kwargs):
    """
    Send text with configurable speed (0-100).

    Args:
        text: The text to send.
        speed: Animation speed (0-100). Defaults to 80.
        char_height: Character height (auto-detected from device if not specified).
                      Defaults to 16 for the 64x16 panel.
        **kwargs: Forwarded to send_text (color, bg_color, font, device_info, ...).

    Returns:
        A SendPlan wrapping the text-send command.
    """
    if 'char_height' not in kwargs:
        kwargs['char_height'] = 16
    return send_text(text, speed=speed, **kwargs)


__all__ = ['text_speed', 'TextAnimation']
