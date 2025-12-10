# -*- coding: utf-8 -*-
"""Text encoding logic for character and emoji blocks."""

from logging import getLogger

from ...lib.emoji_manager import is_emoji
from .models import SegmentType, TextSegment
from .image_processing import (
    render_text_segment_to_chunks, encode_char_img, emoji_to_hex, char_to_hex
)

logger = getLogger(__name__)


def _logic_reverse_bits_order_bytes(data: bytes) -> bytes:
    """Reverse the bit order in each byte independently.
    
    Args:
        data: Bytes to reverse
        
    Returns:
        Bytes with bit order reversed in each byte
    """
    result = bytearray()
    for byte in data:
        reversed_byte = 0
        for i in range(8):
            if (byte >> i) & 1:
                reversed_byte |= 1 << (7 - i)
        result.append(reversed_byte)
    return bytes(result)


def encode_emoji_block(emoji_bytes: bytes, text_size: int) -> bytes:
    """Build the encoded bytes for an emoji block (JPEG format).
    
    Args:
        emoji_bytes (bytes): The JPEG bytes of the emoji.
        text_size (int): The height of the text (16 or 32).
        
    Returns:
        bytes: The encoded emoji block with appropriate header and payload.
    """
    result = bytearray()
    
    if text_size == 32:
        result += bytes([0x09])  # Emoji 32x32
        result += len(emoji_bytes).to_bytes(2, byteorder='little')  # Payload size
        result += bytes([0x00])  # Reserved
    else:  # text_size == 16
        result += bytes([0x08])  # Emoji 16x16 (JPEG format)
        result += len(emoji_bytes).to_bytes(2, byteorder='little')  # Payload size
        result += bytes([0x00])  # Reserved
    
    result += emoji_bytes
    return bytes(result)


def encode_character_block(char_bytes: bytes, text_size: int, color_bytes: bytes) -> bytes:
    """Build the encoded bytes for a character or chunk block.

    Args:
        char_bytes (bytes): The raw character/chunk bitmap bytes.
        text_size (int): The height of the text (16 or 32).
        color_bytes (bytes): The RGB color bytes.

    Returns:
        bytes: The encoded character block with appropriate header and payload.
    """
    result = bytearray()

    if text_size == 32:
        result += bytes([0x02])  # Char 32x16
        result += color_bytes
    else:  # text_size == 16
        result += bytes([0x00])  # Char 16x8
        result += color_bytes

    result += char_bytes
    return bytes(result)


def encode_text_chunked(text: str, char_height: int, color: str, font_path: str, font_offset: tuple[int, int], font_size: int, pixel_threshold: int, chunk_width: int, reverse: bool = False) -> tuple[bytes, int]:
    """Encode text with variable width chunks, handling both regular text and emojis.
    
    This function processes text segment by segment:
    - Regular text portions are rendered as a continuous image and split into chunks
    - Emojis are encoded as JPEG directly
    
    Args:
        text (str): The text to encode.
        char_height (int): The height of the character used for rendering.
        color (str): The color in hex format (e.g., 'ffffff').
        font_path (str): Path to the font file.
        font_offset (tuple[int, int]): The (x, y) offset for the font.
        font_size (int): The font size for rendering.
        pixel_threshold (int): Threshold for pixel conversion.
        chunk_width (int): Width of each chunk in pixels.
        reverse (bool): If True, reverses the order of items. Defaults to False.
    
    Returns:
        tuple: (encoded_bytes, num_items) where num_items is the count of chunks and emojis generated.
    """
    # Convert color to bytes
    try:
        color_bytes = bytes.fromhex(color)
    except Exception:
        raise ValueError(f"Invalid color hex: {color}")
    
    if len(color_bytes) != 3:
        raise ValueError("Color must be 3 bytes (6 hex chars), e.g. 'ffffff'")
    
    items = []  
    segments: list[TextSegment] = []
    current_text = ""
    
    #################
    # Segment Text  #
    #################
    
    for char in text:
        if is_emoji(char):
            # Save current text segment if exists
            if current_text:
                segments.append(TextSegment(SegmentType.TEXT, current_text))
                current_text = ""
            segments.append(TextSegment(SegmentType.EMOJI, char))
        else:
            current_text += char
    
    # Add remaining text segment
    if current_text:
        segments.append(TextSegment(SegmentType.TEXT, current_text))
    
    ####################
    # Process Segments #
    ####################
    
    for segment in segments:
        if segment.is_emoji:
            emoji_bytes = emoji_to_hex(segment.content, char_height)
            if emoji_bytes:
                items.append(encode_emoji_block(emoji_bytes, char_height))
        else:
            # Render text segment and split into chunks
            chunks = render_text_segment_to_chunks(segment.content, char_height, font_path, 
                                                    font_offset, font_size, pixel_threshold, chunk_width)
            
            # Encode each chunk as an item
            for chunk in chunks:
                char_bytes = encode_char_img(chunk)
                char_bytes = _logic_reverse_bits_order_bytes(char_bytes)
                items.append(encode_character_block(char_bytes, char_height, color_bytes))
    
    ###################
    # Final Assembly  #
    ###################
    
    # Reverse items if needed (for RTL)
    if reverse:
        items.reverse()
    
    # Combine all items
    result = bytearray()
    for item in items:
        result += item
    
    return bytes(result), len(items)


def encode_text(text: str, matrix_height: int, color: str, font_path: str, font_offset: tuple[int, int], font_size: int, pixel_threshold: int, reverse: bool = False) -> bytes:
    """Encode text to be displayed on the device.

    Args:
        text (str): The text to encode.
        matrix_height (int): The height of the LED matrix.
        color (str): The color in hex format (e.g., 'ffffff').
        font_path (str): Path to the font file.
        font_offset (tuple[int, int]): The (x, y) offset for the font.
        font_size (int): The font size for rendering.
        pixel_threshold (int): Threshold for pixel conversion.
        reverse (bool): If True, reverses the order of characters. Defaults to False.

    Returns:
        bytes: The encoded text as raw bytes ready to be appended to a payload.
    """
    result = bytearray()

    # Convert color to bytes
    try:
        color_bytes = bytes.fromhex(color)
    except Exception:
        raise ValueError(f"Invalid color hex: {color}")
    
    # Validate color length
    if len(color_bytes) != 3:
        raise ValueError("Color must be 3 bytes (6 hex chars), e.g. 'ffffff'")

    # Reverse text if requested
    text_to_process = text[::-1] if reverse else text

    ##############
    # Processing #
    ##############

    for char in text_to_process:
        if is_emoji(char):
            char_bytes = emoji_to_hex(char, matrix_height)
            if char_bytes:
                result += encode_emoji_block(char_bytes, matrix_height)
            else:
                logger.error(f"Failed to encode emoji: {char}")
        else:
            char_bytes = char_to_hex(char, matrix_height, font_path, font_offset, font_size, pixel_threshold)
            if char_bytes:
                char_bytes = _logic_reverse_bits_order_bytes(char_bytes)
                result += encode_character_block(char_bytes, matrix_height, color_bytes)
            else:
                logger.error(f"Failed to encode character: {char}")

    return bytes(result)
