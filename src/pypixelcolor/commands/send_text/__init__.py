# -*- coding: utf-8 -*-
"""Text command module with support for emojis, per-character colors, and variable-width rendering."""

import binascii
from typing import Optional, Union
from logging import getLogger

from ...lib.transport.send_plan import SendPlan, Window
from ...lib.device_info import DeviceInfo
from ...lib.font_config import FontConfig

from .models import RenderContext
from .font_utils import resolve_font_config, get_char_height_from_device
from .encoding import encode_text_chunked, encode_text
from .color_utils import has_color_tags, strip_color_tags, parse_colored_text, parse_hex_color

logger = getLogger(__name__)


def build_text_properties(
    animation: int,
    speed: int,
    rainbow_mode: int,
    color_bytes: bytes,
    bg_color_bytes: Optional[bytes] = None,
) -> bytes:
    """Construct the 13-byte properties header for text display."""
    properties = bytearray([0x00, 0x01, 0x01])
    properties.extend([
        int(animation) & 0xFF,
        int(speed) & 0xFF,
        int(rainbow_mode) & 0xFF,
    ])
    properties.extend(color_bytes)

    if bg_color_bytes is not None:
        properties.append(0x01)
        properties.extend(bg_color_bytes)
    else:
        properties.extend([0x00, 0x00, 0x00, 0x00])

    return bytes(properties)


def build_text_send_plan(data_payload: bytes, save_slot: int = 0) -> SendPlan:
    """Split data payload into 12KB multi-frame transport windows."""
    crc = binascii.crc32(data_payload) & 0xFFFFFFFF
    payload_size = len(data_payload)

    windows = []
    window_size = 12 * 1024
    pos = 0
    window_index = 0

    while pos < payload_size:
        window_end = min(pos + window_size, payload_size)
        chunk_payload = data_payload[pos:window_end]

        option = 0x00 if window_index == 0 else 0x02

        frame_header = bytearray([0x00, 0x01, option])
        frame_header += payload_size.to_bytes(4, byteorder="little")
        frame_header += crc.to_bytes(4, byteorder="little")
        frame_header += bytes([0x00, int(save_slot) & 0xFF])

        frame_content = frame_header + chunk_payload
        prefix = (len(frame_content) + 2).to_bytes(2, byteorder="little")

        windows.append(Window(data=prefix + frame_content, requires_ack=True))
        window_index += 1
        pos = window_end

    logger.debug(f"Split text into {len(windows)} frames")
    return SendPlan("send_text", windows)


def send_text(text: str,
              rainbow_mode: int = 0,
              animation: int = 0,
              save_slot: int = 0,
              speed: int = 80,
              color: str = "ffffff",
              bg_color: Optional[str] = None,
              font: Union[str, FontConfig] = "UNIFONT",
              char_height: Optional[int] = None,
              font_size: Optional[int] = None,
              font_offset: Optional[tuple[int, int]] = None,
              pixel_threshold: Optional[int] = None,
              var_width: Optional[Union[bool, str]] = None,
              device_info: Optional[DeviceInfo] = None
              ) -> SendPlan:
    """
    Send a text to the device with configurable parameters.
    If emojis are included in the text, they will be rendered using Twemoji.

    Args:
        text (str): The text to send. Supports inline color tags (e.g. '[#ff0000]Hello[/]').
        rainbow_mode (int, optional): Rainbow mode (0-9). Defaults to 0.
        animation (int, optional): Animation type (0-7, except 3 and 4). Defaults to 0.
        save_slot (int, optional): Save slot (1-10). Defaults to 1.
        speed (int, optional): Animation speed (0-100). Defaults to 80.
        color (str, optional): Default text color in hex. Defaults to "ffffff".
        bg_color (str, optional): Background color in hex (e.g., "ff0000"). Defaults to None.
        font (str | FontConfig, optional): Font name, file path, or FontConfig. Defaults to "UNIFONT".
        char_height (int, optional): Character height. Auto-detected from device_info if not specified.
        font_size (int, optional): Manual font size override.
        font_offset (tuple[int, int], optional): Manual font offset override (x, y).
        pixel_threshold (int, optional): Manual pixel threshold override (0-255).
        var_width (bool, optional): Override variable width mode.
        device_info (DeviceInfo, optional): Device information (injected automatically).

    Raises:
        ValueError: If an invalid animation is selected or parameters are out of range.
    """
    # 1. Resolve font configuration and character height
    font_config = resolve_font_config(font)

    if char_height is None:
        if device_info is not None:
            char_height = get_char_height_from_device(device_info)
        else:
            raise ValueError("char_height must be specified if device_info is not provided")

    char_height = int(char_height)
    metrics = font_config.get_metrics(char_height)

    # 2. Resolve rendering parameters into a RenderContext
    resolved_font_size = int(metrics["font_size"]) if font_size is None else int(font_size)

    if font_offset is None:
        resolved_offset = tuple(metrics["offset"])
    elif isinstance(font_offset, str):
        cleaned = font_offset.strip("()[] ")
        parts = [int(p.strip()) for p in cleaned.split(",")]
        resolved_offset = (parts[0], parts[1])
    else:
        resolved_offset = (int(font_offset[0]), int(font_offset[1]))

    resolved_threshold = int(metrics["pixel_threshold"]) if pixel_threshold is None else int(pixel_threshold)

    context = RenderContext(
        char_height=char_height,
        font_path=font_config.path,
        font_size=resolved_font_size,
        font_offset=resolved_offset,
        pixel_threshold=resolved_threshold,
    )

    # 3. Resolve var_width mode
    if var_width is not None:
        resolved_var_width = var_width.lower() in ("true", "1", "yes", "y") if isinstance(var_width, str) else bool(var_width)
    else:
        resolved_var_width = bool(metrics.get("var_width", False))

    # 4. Handle inline color tags
    if resolved_var_width:
        if has_color_tags(text):
            logger.warning("Color tags are not supported with var_width and will be ignored.")
            clean_text = strip_color_tags(text)
        else:
            clean_text = text
        char_colors = None
    else:
        clean_text, char_colors = parse_colored_text(text, color)

    # 5. Parse and validate colors
    color_bytes = parse_hex_color(color, "Color")
    bg_color_bytes = parse_hex_color(bg_color, "Background color") if bg_color is not None else None

    # 6. Validate parameter ranges
    checks = [
        (int(rainbow_mode), 0, 9, "Rainbow mode"),
        (int(animation), 0, 7, "Animation"),
        (int(save_slot), 0, 255, "Save slot"),
        (int(speed), 0, 100, "Speed"),
        (len(clean_text), 1, 500, "Text length"),
        (char_height, 1, 128, "Char height"),
    ]
    for param, min_val, max_val, name in checks:
        if not (min_val <= param <= max_val):
            raise ValueError(f"{name} must be between {min_val} and {max_val} (got {param})")

    if device_info and (device_info.height != 32 or device_info.width != 32):
        if int(animation) in (3, 4):
            raise ValueError("This animation is not supported with this font on non-32x32 devices.")

    # 7. Encode characters
    rtl = (int(animation) == 2)

    if resolved_var_width:
        actual_chunk_width = 8 if char_height <= 20 else 16
        characters_bytes, num_chars = encode_text_chunked(
            clean_text, color_bytes, context, actual_chunk_width, reverse=rtl
        )
    else:
        characters_bytes = encode_text(
            clean_text, color_bytes, context, reverse=rtl, char_colors=char_colors
        )
        num_chars = len(clean_text)

    # 8. Assemble data payload and generate transport send plan
    properties = build_text_properties(animation, speed, rainbow_mode, color_bytes, bg_color_bytes)
    data_payload = bytes([num_chars]) + properties + characters_bytes

    return build_text_send_plan(data_payload, save_slot=int(save_slot))


__all__ = ['send_text']
