# -*- coding: utf-8 -*-
"""Text command module with support for emojis and variable-width rendering."""

import binascii
from typing import Optional, Union
from logging import getLogger

from ...lib.transport.send_plan import SendPlan, Window
from ...lib.device_info import DeviceInfo
from ...lib.font_config import FontConfig

from .font_utils import resolve_font_config, get_char_height_from_device
from .encoding import encode_text_chunked, encode_text

logger = getLogger(__name__)


def send_text(text: str,
              rainbow_mode: int = 0,
              animation: int = 0,
              save_slot: int = 0,
              speed: int = 80,
              color: str = "ffffff",
              bg_color: Optional[str] = None,
              font: Union[str, FontConfig] = "CUSONG",
              char_height: Optional[int] = None,
              device_info: Optional[DeviceInfo] = None
              ):
    """
    Send a text to the device with configurable parameters.
    If emojis are included in the text, they will be rendered using Twemoji.

    Args:
        text (str): The text to send.
        rainbow_mode (int, optional): Rainbow mode (0-9). Defaults to 0.
        animation (int, optional): Animation type (0-7, except 3 and 4). Defaults to 0.
        save_slot (int, optional): Save slot (1-10). Defaults to 1.
        speed (int, optional): Animation speed (0-100). Defaults to 80.
        color (str, optional): Text color in hex. Defaults to "ffffff".
        bg_color (str, optional): Background color in hex (e.g., "ff0000" for red). Defaults to None (no background).
        font (str | FontConfig, optional): Built-in font name, file path, or FontConfig object. Defaults to "CUSONG". Built-in fonts are "CUSONG", "SIMSUN", "VCR_OSD_MONO".
        char_height (int, optional): Character height. Auto-detected from device_info if not specified.
        device_info (DeviceInfo, optional): Device information (injected automatically by DeviceSession).

    Returns:
        bytes: Encoded command to send to the device.

    Raises:
        ValueError: If an invalid animation is selected or parameters are out of range.
    """
    
    # Resolve font configuration
    font_config = resolve_font_config(font)

    # Auto-detect char_height from device_info if available
    if char_height is None:
        if device_info is not None:
            char_height = get_char_height_from_device(device_info)
            logger.debug(f"Auto-detected matrix height from device (height={device_info.height}): {char_height}")
        else:
            raise ValueError("char_height must be specified if device_info is not provided")
    
    char_height = int(char_height)
    
    # Get metrics for this character height
    metrics = font_config.get_metrics(char_height)
    font_size = metrics["font_size"]
    font_offset = metrics["offset"]
    pixel_threshold = metrics["pixel_threshold"]
    var_width = metrics["var_width"]
    
    # properties: 3 fixed bytes + animation + speed + rainbow + 3 bytes color + 1 byte bg flag + 3 bytes bg color
    try:
        color_bytes = bytes.fromhex(color)
    except Exception:
        raise ValueError(f"Invalid color hex: {color}")
    if len(color_bytes) != 3:
        raise ValueError("Color must be 3 bytes (6 hex chars), e.g. 'ffffff'")

    # Validate parameter ranges
    checks = [
        (int(rainbow_mode), 0, 9, "Rainbow mode"),
        (int(animation), 0, 7, "Animation"),
        (int(save_slot), 0, 255, "Save slot"),
        (int(speed), 0, 100, "Speed"),
        (len(text), 1, 500, "Text length"),
        (char_height, 1, 128, "Char height"),
    ]
    for param, min_val, max_val, name in checks:
        if not (min_val <= param <= max_val):
            raise ValueError(f"{name} must be between {min_val} and {max_val} (got {param})")

    # Disable unsupported animations (bootloop)
    if device_info and (device_info.height != 32 or device_info.width != 32):
        if (int(animation) == 3 or int(animation) == 4):
            raise ValueError("This animation is not supported with this font on non-32x32 devices.")

    # Determine if RTL mode should be enabled (only for animation 2)
    rtl = (int(animation) == 2)
    if rtl:
        logger.debug("Reversed chunk order for RTL display")

    #---------------- BUILD PAYLOAD ----------------#

    #########################
    #       PROPERTIES      #
    #########################

    properties = bytearray()
    properties += bytes([
        0x00,   # Reserved
        0x01,   # Reserved
        0x01    # Reserved
    ])
    properties += bytes([
        int(animation) & 0xFF,      # Animation
        int(speed) & 0xFF,          # Speed
        int(rainbow_mode) & 0xFF    # Rainbow mode
    ])
    properties += color_bytes

    # Trailing 4 bytes - Background color: [enable_flag, R, G, B]
    if bg_color is not None:
        try:
            bg_color_bytes = bytes.fromhex(bg_color)
        except Exception:
            raise ValueError(f"Invalid background color hex: {bg_color}")
        if len(bg_color_bytes) != 3:
            raise ValueError("Background color must be 3 bytes (6 hex chars), e.g. 'ff0000'")
        properties += bytes([0x01])  # Enable background
        properties += bg_color_bytes
        logger.info(f"Background color enabled: #{bg_color}")
    else:
        properties += bytes([
            0x00,   # Background disabled
            0x00,   # R (unused)
            0x00,   # G (unused)
            0x00    # B (unused)
        ])

    #########################
    #       CHARACTERS      #
    #########################

    if var_width:
        # Determine chunk width based on char_height
        chunk_width = 8  if char_height <= 20 else 16

        # Encode text with chunks and emoji support, getting both bytes and item count
        characters_bytes, num_chars = encode_text_chunked(
            text,
            char_height,
            color,
            font_config.path,
            font_offset,
            font_size,
            pixel_threshold,
            chunk_width,
            reverse=rtl
        )
    else:
        # Original character-by-character encoding
        characters_bytes = encode_text(
            text,
            char_height,
            color,
            font_config.path,
            font_offset,
            font_size,
            pixel_threshold,
            reverse=rtl
        )

        # Number of characters is the length of the text
        num_chars = len(text)

    # Build data payload with character count
    data_payload = bytes([num_chars]) + properties + characters_bytes

    #########################
    #        CHECKSUM       #
    #########################

    crc = binascii.crc32(data_payload) & 0xFFFFFFFF
    payload_size = len(data_payload)

    #########################
    #      MULTI-FRAME      #
    #########################

    windows = []
    window_size = 12 * 1024
    pos = 0
    window_index = 0
    
    while pos < payload_size:
        window_end = min(pos + window_size, payload_size)
        chunk_payload = data_payload[pos:window_end]
        
        # Option: 0x00 for first frame, 0x02 for subsequent frames
        option = 0x00 if window_index == 0 else 0x02
        
        # Construct header for this frame
        # [00 01 Option] [Payload Size (4)] [CRC (4)] [00 SaveSlot]
        
        frame_header = bytearray()
        frame_header += bytes([
            0x00,   # Reserved
            0x01,   # Command
            option  # Option
        ])
        
        # Payload Size (Total) - 4 bytes little endian
        frame_header += payload_size.to_bytes(4, byteorder="little")
        
        # CRC - 4 bytes little endian
        frame_header += crc.to_bytes(4, byteorder="little")
        
        # Tail - 2 bytes
        frame_header += bytes([0x00])                   # Reserved
        frame_header += bytes([int(save_slot) & 0xFF])  # save_slot
        
        # Combine header and chunk
        frame_content = frame_header + chunk_payload
        
        # Calculate frame length prefix
        # Total size = len(frame_content) + 2 (for the prefix itself)
        frame_len = len(frame_content) + 2
        prefix = frame_len.to_bytes(2, byteorder="little")
        
        message = prefix + frame_content
        windows.append(Window(data=message, requires_ack=True))
        
        window_index += 1
        pos = window_end

    logger.info(f"Split text into {len(windows)} frames")
    return SendPlan("send_text", windows)


# Export public API
__all__ = ['send_text']
