# -*- coding: utf-8 -*-
"""Text encoding logic for character and emoji blocks."""

from logging import getLogger
from typing import Optional

from ...lib.emoji_manager import is_emoji
from .models import SegmentType, TextSegment, RenderContext
from .image_processing import (
    render_text_segment_to_chunks, encode_char_img, emoji_to_hex, char_to_hex
)

logger = getLogger(__name__)


def _logic_reverse_bits_order_bytes(data: bytes) -> bytes:
    """Reverse the bit order in each byte independently."""
    result = bytearray()
    for byte in data:
        reversed_byte = 0
        for i in range(8):
            if (byte >> i) & 1:
                reversed_byte |= 1 << (7 - i)
        result.append(reversed_byte)
    return bytes(result)


def encode_emoji_block(emoji_bytes: bytes, text_size: int) -> bytes:
    """Build the encoded bytes for an emoji block (JPEG format)."""
    opcode = 0x09 if text_size >= 32 else 0x08
    return bytes([opcode]) + len(emoji_bytes).to_bytes(2, byteorder='little') + bytes([0x00]) + emoji_bytes


def encode_character_block(char_bytes: bytes, text_size: int, color_bytes: bytes, char_width: int | None = None) -> bytes:
    """Build the encoded bytes for a character or chunk block."""
    is_32 = 1 if text_size >= 32 else 0
    if char_width is None:
        bytes_per_line = len(char_bytes) // text_size if text_size > 0 else 1
        is_wide = 1 if bytes_per_line > (2 if is_32 else 1) else 0
    else:
        is_wide = 1 if char_width > (16 if is_32 else 8) else 0

    opcode = (is_32 << 1) | is_wide

    result = bytearray()
    result.append(opcode)
    result.extend(color_bytes)
    result.extend(char_bytes)
    return bytes(result)


def encode_text_chunked(
    text: str,
    color_bytes: bytes,
    context: RenderContext,
    chunk_width: int,
    reverse: bool = False,
) -> tuple[bytes, int]:
    """Encode text with variable width chunks, handling both regular text and emojis.

    Args:
        text (str): The text to encode.
        color_bytes (bytes): 3-byte RGB text color.
        context (RenderContext): Font rendering parameters.
        chunk_width (int): Width of each chunk in pixels.
        reverse (bool): If True, reverses the order of items. Defaults to False.

    Returns:
        tuple[bytes, int]: (encoded_bytes, num_items)
    """
    items = []
    segments: list[TextSegment] = []
    current_text = ""

    # Segment text into regular strings and emojis
    for char in text:
        if is_emoji(char):
            if current_text:
                segments.append(TextSegment(SegmentType.TEXT, current_text))
                current_text = ""
            segments.append(TextSegment(SegmentType.EMOJI, char))
        else:
            current_text += char

    if current_text:
        segments.append(TextSegment(SegmentType.TEXT, current_text))

    # Process segments
    for segment in segments:
        if segment.is_emoji:
            emoji_bytes = emoji_to_hex(segment.content, context.char_height)
            if emoji_bytes:
                items.append(encode_emoji_block(emoji_bytes, context.char_height))
        else:
            chunks = render_text_segment_to_chunks(segment.content, context, chunk_width)
            for chunk in chunks:
                char_bytes = encode_char_img(chunk)
                char_bytes = _logic_reverse_bits_order_bytes(char_bytes)
                items.append(encode_character_block(char_bytes, context.char_height, color_bytes, char_width=chunk.width))

    if reverse:
        items.reverse()

    result = bytearray()
    for item in items:
        result += item

    return bytes(result), len(items)


def encode_text(
    text: str,
    color_bytes: bytes,
    context: RenderContext,
    reverse: bool = False,
    char_colors: Optional[list[str]] = None,
) -> bytes:
    """Encode text character-by-character to be displayed on the device.

    Args:
        text (str): The text to encode.
        color_bytes (bytes): Default 3-byte RGB text color.
        context (RenderContext): Font rendering parameters.
        reverse (bool): If True, reverses the order of characters. Defaults to False.
        char_colors (list[str], optional): List of hex colors for each character in text.

    Returns:
        bytes: Encoded bytes for all characters and emojis.
    """
    result = bytearray()

    # Process per-character colors if provided
    colors_to_process = None
    if char_colors is not None:
        colors_to_process = []
        for c in char_colors:
            try:
                cb = bytes.fromhex(c)
                if len(cb) != 3:
                    cb = color_bytes
            except Exception:
                cb = color_bytes
            colors_to_process.append(cb)

    # Reverse text and colors if requested (for RTL)
    if reverse:
        text_to_process = text[::-1]
        if colors_to_process is not None:
            colors_to_process = colors_to_process[::-1]
    else:
        text_to_process = text

    for idx, char in enumerate(text_to_process):
        current_color = colors_to_process[idx] if colors_to_process is not None and idx < len(colors_to_process) else color_bytes
        if is_emoji(char):
            char_bytes = emoji_to_hex(char, context.char_height)
            if char_bytes:
                result += encode_emoji_block(char_bytes, context.char_height)
            else:
                logger.error(f"Failed to encode emoji: {char}")
        else:
            char_bytes, char_width = char_to_hex(char, context)
            if char_bytes:
                char_bytes = _logic_reverse_bits_order_bytes(char_bytes)
                result += encode_character_block(char_bytes, context.char_height, current_color, char_width=char_width)
            else:
                logger.error(f"Failed to encode character: {char}")

    return bytes(result)
