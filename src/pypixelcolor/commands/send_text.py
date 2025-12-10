# -*- coding: utf-8 -*-

# Imports
import os
import binascii
from enum import Enum
from dataclasses import dataclass
from PIL import Image, ImageDraw, ImageFont
from logging import getLogger
from typing import Optional, Union
from io import BytesIO

# Locals
from ..lib.transport.send_plan import SendPlan, Window
from ..lib.device_info import DeviceInfo
from ..lib.font_config import FontConfig, BUILTIN_FONTS
from ..lib.emoji_manager import is_emoji, get_emoji_image

logger = getLogger(__name__)


class SegmentType(Enum):
    """Type of text segment."""
    TEXT = "text"
    EMOJI = "emoji"


@dataclass
class TextSegment:
    """A segment of text, either regular characters or an emoji."""
    type: SegmentType
    content: str
    
    @property
    def is_emoji(self) -> bool:
        return self.type == SegmentType.EMOJI
    
    @property
    def is_text(self) -> bool:
        return self.type == SegmentType.TEXT

# Helper functions for byte-level transformations

def _reverse_bits_16(n: int) -> int:
    """Reverse bits in a 16-bit integer."""
    n = ((n & 0xFF00) >> 8) | ((n & 0x00FF) << 8)
    n = ((n & 0xF0F0) >> 4) | ((n & 0x0F0F) << 4)
    n = ((n & 0xCCCC) >> 2) | ((n & 0x3333) << 2)
    n = ((n & 0xAAAA) >> 1) | ((n & 0x5555) << 1)
    return n

def _logic_reverse_bits_order_bytes(data: bytes) -> bytes:
    """Reverse bit order in each 16-bit chunk.
    Args:
        data (bytes): Input byte data.
    Returns:
        bytes: Bit-reversed byte data.
    """
    if len(data) % 2 != 0:
        raise ValueError("Data length must be multiple of 2 bytes for bit reversal")
    out = bytearray()
    for i in range(0, len(data), 2):
        chunk = data[i:i+2]
        # Read as little-endian to avoid double reversal
        value = int.from_bytes(chunk, byteorder="little")
        rev = _reverse_bits_16(value)
        out += rev.to_bytes(2, byteorder="big")
    return bytes(out)

# Helper function to resolve font configuration

def _resolve_font_config(font: Union[str, FontConfig]) -> FontConfig:
    """Resolve a font specification to a FontConfig object.
    
    Args:
        font: Either a built-in font name (str), a file path (str), or a FontConfig object
        
    Returns:
        FontConfig object
        
    Raises:
        ValueError: If the font cannot be resolved
    """
    if isinstance(font, FontConfig):
        return font
    
    if not isinstance(font, str):
        raise ValueError(f"Font must be a string or FontConfig, got {type(font)}")
    
    # Try built-in fonts first
    if font in BUILTIN_FONTS:
        return BUILTIN_FONTS[font]
    
    # Try loading as file path
    if os.path.exists(font):
        return FontConfig.from_file(font)
    
    # Fallback to default font
    logger.warning(f"Font '{font}' not found. Using default font CUSONG.")
    return BUILTIN_FONTS["CUSONG"]


def _get_char_height_from_device(device_info: DeviceInfo) -> int:
    """Map device dimensions to appropriate character height.
    
    This function returns a suitable character height based on the device's
    physical dimensions. Heights are mapped as follows:
    - 8 pixels:   devices with height <= 8 (small single-line displays)
    - 16 pixels:  devices with height between 9 and 20 (most common)
    - 32 pixels:  devices with height > 20 (large displays like 32x32)
    
    Args:
        device_info (DeviceInfo): Device information with width and height.
        
    Returns:
        int: The recommended character height (8, 16, or 32).
    """
    if device_info.height <= 20:
        return 16
    else:
        return device_info.height


# Helper functions for PIL operations

def _apply_pixel_threshold(img: Image.Image, threshold: int) -> Image.Image:
    """Apply threshold to convert grayscale image to binary.
    
    Args:
        img (Image.Image): Input grayscale image.
        threshold (int): Pixel value threshold (0-255).
    
    Returns:
        Image.Image: Binary image (black/white only).
    """
    return img.point(lambda p: 255 if p > threshold else 0, mode='L')


def _create_text_image(text: str, height: int, font_path: str, 
                       offset: tuple[int, int], font_size: int, 
                       pixel_threshold: int) -> tuple[Image.Image, dict]:
    """Create a PIL image from text with threshold applied.
    
    Args:
        text (str): Text to render.
        height (int): Image height in pixels.
        font_path (str): Path to font file.
        offset (tuple[int, int]): (x, y) offset for text rendering.
        font_size (int): Font size in points.
        pixel_threshold (int): Threshold for binary conversion (0-255).
    
    Returns:
        tuple: (image, metadata) where metadata dict contains:
            - 'bbox': Bounding box tuple (x0, y0, x1, y1)
            - 'width': Text width in pixels
            - 'draw': ImageDraw object (for further drawing if needed)
            - 'font': ImageFont object
    """
    img = Image.new('L', (1000, height), 0)
    draw = ImageDraw.Draw(img)
    font_obj = ImageFont.truetype(font_path, font_size)
    
    # Draw text
    draw.text(offset, text, fill=255, font=font_obj)
    
    # Apply threshold
    img = _apply_pixel_threshold(img, pixel_threshold)
    
    # Get dimensions
    bbox = draw.textbbox((0, 0), text, font=font_obj)
    text_width = bbox[2] - bbox[0]
    
    return img, {'bbox': bbox, 'width': text_width, 'draw': draw, 'font': font_obj}


def _render_text_segment_to_chunks(text: str, height: int, font_path: str, 
                                   offset: tuple[int, int], font_size: int, 
                                   pixel_threshold: int, chunk_width: int) -> list[Image.Image]:
    """Render text segment and split into fixed-width chunks.
    
    Args:
        text (str): Text to render.
        height (int): Image height in pixels.
        font_path (str): Path to font file.
        offset (tuple[int, int]): (x, y) offset for text rendering.
        font_size (int): Font size in points.
        pixel_threshold (int): Threshold for binary conversion.
        chunk_width (int): Width of each chunk in pixels.
    
    Returns:
        list[Image.Image]: List of image chunks.
    """
    img, meta = _create_text_image(text, height, font_path, offset, font_size, pixel_threshold)
    # Crop to actual text width with padding
    img = img.crop((0, 0, meta['width'] + 4, height))
    return _split_image_into_chunks(img, chunk_width)



def _encode_char_img(img: Image.Image) -> bytes:
    """
    Convert a character image to a bytes representation (one line after another).

    Returns:
        bytes: Encoded byte data of the character image.
    """

    # Load the image in grayscale and get dimensions
    img = img.convert("L")
    char_width, char_height = img.size

    if img.size != (char_width, char_height):
        raise ValueError("The image must be " + str(char_width) + "x" + str(char_height) + " pixels")

    data_bytes = bytearray()
    logger.debug("=" * char_width + " %i" % char_width)

    for y in range(char_height):
        line_value = 0
        line_value_2 = 0

        for x in range(char_width):
            pixel = img.getpixel((x, y))
            if pixel > 0:  # type: ignore
                if x < 16:
                    line_value |= (1 << (15 - x))
                else:
                    line_value_2 |= (1 << (31 - x))

        # Merge line_value_2 into line_value for 32-bit value
        line_value = (line_value_2) | (line_value << 16) if char_width > 16 else line_value

        # Build the line bytes (big-endian) according to width
        if char_width <= 8:
            line_value >>= 8
            byte_len = 1
            binary_str = f"{line_value:0{8}b}".replace('0', '.').replace('1', '#')
        elif char_width <= 16:
            byte_len = 2
            binary_str = f"{line_value:0{16}b}".replace('0', '.').replace('1', '#')
        elif char_width <= 24:
            line_value >>= 8
            byte_len = 3
            binary_str = f"{line_value:0{24}b}".replace('0', '.').replace('1', '#')
        else:
            byte_len = 4
            binary_str = f"{line_value:0{32}b}".replace('0', '.').replace('1', '#')

        logger.debug(binary_str)

        data_bytes += line_value.to_bytes(byte_len, byteorder='big')

    return bytes(data_bytes)


def _emoji_to_hex(emoji: str, emoji_height: int) -> Optional[bytes]:
    """Convert an emoji to JPEG bytes.
    
    Args:
        emoji (str): The emoji character to convert.
        emoji_height (int): The size of the emoji (height of the matrix).
        
    Returns:
        Optional[bytes]: JPEG bytes of the emoji, or None if conversion fails.
    """
    try:
        # Download and load emoji image from Twemoji
        img = get_emoji_image(emoji, size=emoji_height)
        
        if img is None:
            logger.error(f"Failed to get emoji image for {emoji}")
            return None
        
        # Convert to JPEG format
        buffer = BytesIO()
        img.save(buffer, format='JPEG', quality=95, subsampling=0, optimize=True)
        jpeg_bytes = buffer.getvalue()
        
        # Remove JFIF header if present and replace with quantization tables only
        # Official app uses raw JPEG without JFIF metadata
        if jpeg_bytes[2:4] == b'\xff\xe0':  # JFIF marker
            # Find DQT (Define Quantization Table) marker
            dqt_pos = jpeg_bytes.find(b'\xff\xdb')
            if dqt_pos > 0:
                # Rebuild JPEG: SOI + DQT + rest (skip JFIF)
                jpeg_bytes = b'\xff\xd8' + jpeg_bytes[dqt_pos:]
        
        return jpeg_bytes
    except Exception as e:
        logger.error(f"Error rendering emoji {emoji}: {e}")
        return None


def _char_to_hex(character: str, char_height: int, font_path: str, font_offset: tuple[int, int], font_size: int, pixel_threshold: int) -> Optional[bytes]:
    """Convert a character to its bitmap bytes.
    
    Args:
        character (str): The character to convert.
        char_height (int): The size of the text (height of the matrix).
        font_path (str): The path to the font file.
        font_offset (tuple[int, int]): The (x, y) offset for the font.
        font_size (int): The font size to use for rendering.
        pixel_threshold (int): Threshold for converting grayscale to binary.
        
    Returns:
        Optional[bytes]: Encoded bitmap bytes of the character, or None if conversion fails.
    """
    try:
        # Generate image with dynamic width
        # First, create a temporary large image to measure text in grayscale
        temp_img = Image.new('L', (100, char_height), 0)
        temp_draw = ImageDraw.Draw(temp_img)
        font_obj = ImageFont.truetype(font_path, font_size)
        
        # Get text bounding box
        bbox = temp_draw.textbbox((0, 0), character, font=font_obj)
        text_width = bbox[2] - bbox[0]

        # Clamp text_width between min and max values to prevent crash
        if char_height == 32:
            min_width = 9
            max_width = 16
        else:
            min_width = 1
            max_width = 8
        text_width = int(max(min_width, min(text_width, max_width)))

        # Create final image in grayscale mode for pixel-perfect rendering
        img = Image.new('L', (int(text_width), int(char_height)), 0)
        d = ImageDraw.Draw(img)
        
        # Draw text in white (255) for pixel-perfect rendering
        d.text(font_offset, character, fill=255, font=font_obj)

        # Apply threshold for pixel-perfect conversion
        img = _apply_pixel_threshold(img, pixel_threshold)

        bytes_data = _encode_char_img(img)
        return bytes_data
    except Exception as e:
        logger.error(f"Error occurred while converting character to hex: {e}")
        return None



def _split_image_into_chunks(img: Image.Image, chunk_width: int) -> list[Image.Image]:
    """Split a PIL image into fixed-width vertical chunks.

    Args:
        img (Image.Image): The image to split.
        chunk_width (int): Width of each chunk in pixels.

    Returns:
        list[Image.Image]: List of image chunks, all with width=chunk_width (padded with black if needed).
    """
    width, height = img.size
    chunks = []

    for x in range(0, width, chunk_width):
        # Calculate the actual width of this chunk (last chunk might be narrower)
        actual_width = min(chunk_width, width - x)

        # Crop the chunk from the image
        chunk = img.crop((x, 0, x + actual_width, height))

        # If this chunk is narrower than chunk_width, pad it with black pixels
        if actual_width < chunk_width:
            # Create a new image with the full chunk_width, filled with black (0)
            padded_chunk = Image.new('L', (chunk_width, height), 0)
            # Paste the actual chunk on the left side
            padded_chunk.paste(chunk, (0, 0))
            chunk = padded_chunk
            logger.debug(f"Created chunk {len(chunks)}: {actual_width}x{height} pixels (padded to {chunk_width}x{height}) at x={x}")
        else:
            logger.debug(f"Created chunk {len(chunks)}: {actual_width}x{height} pixels at x={x}")

        chunks.append(chunk)

    return chunks


def _encode_emoji_block(emoji_bytes: bytes, text_size: int) -> bytes:
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


def _encode_character_block(char_bytes: bytes, text_size: int, color_bytes: bytes) -> bytes:
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


def _encode_text_chunked(text: str, char_height: int, color: str, font_path: str, font_offset: tuple[int, int], font_size: int, pixel_threshold: int, chunk_width: int, reverse: bool = False) -> tuple[bytes, int]:
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
            emoji_bytes = _emoji_to_hex(segment.content, char_height)
            if emoji_bytes:
                items.append(_encode_emoji_block(emoji_bytes, char_height))
        else:
            # Render text segment and split into chunks
            chunks = _render_text_segment_to_chunks(segment.content, char_height, font_path, 
                                                    font_offset, font_size, pixel_threshold, chunk_width)
            
            # Encode each chunk as an item
            for chunk in chunks:
                char_bytes = _encode_char_img(chunk)
                char_bytes = _logic_reverse_bits_order_bytes(char_bytes)
                items.append(_encode_character_block(char_bytes, char_height, color_bytes))
    
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

def _encode_text(text: str, matrix_height: int, color: str, font_path: str, font_offset: tuple[int, int], font_size: int, pixel_threshold: int, reverse: bool = False) -> bytes:
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
            char_bytes = _emoji_to_hex(char, matrix_height)
            if char_bytes:
                result += _encode_emoji_block(char_bytes, matrix_height)
            else:
                logger.error(f"Failed to encode emoji: {char}")
        else:
            char_bytes = _char_to_hex(char, matrix_height, font_path, font_offset, font_size, pixel_threshold)
            if char_bytes:
                char_bytes = _logic_reverse_bits_order_bytes(char_bytes)
                result += _encode_character_block(char_bytes, matrix_height, color_bytes)
            else:
                logger.error(f"Failed to encode character: {char}")

    return bytes(result)

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
    font_config = _resolve_font_config(font)

    # Auto-detect char_height from device_info if available
    if char_height is None:
        if device_info is not None:
            char_height = _get_char_height_from_device(device_info)
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
        characters_bytes, num_chars = _encode_text_chunked(
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
        characters_bytes = _encode_text(
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
