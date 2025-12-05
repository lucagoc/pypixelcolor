# -*- coding: utf-8 -*-

# Imports
import os
import binascii
from PIL import Image, ImageDraw, ImageFont
from logging import getLogger
from typing import Optional, Union
from io import BytesIO

# Locals
from ..lib.transport.send_plan import single_window_plan, SendPlan, Window
from ..lib.device_info import DeviceInfo
from ..lib.font_config import FontConfig, BUILTIN_FONTS
from ..lib.emoji_manager import is_emoji, get_emoji_image

logger = getLogger(__name__)

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


def _charimg_to_hex_string(img: Image.Image) -> tuple[bytes, int]:
    """
    Convert a character image to a bytes representation (one line after another).

    Returns:
        tuple: (bytes_data, char_width)
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

    return bytes(data_bytes), char_width


def _char_to_hex(character: str, char_size: int, font_path: str, font_offset: tuple[int, int], font_size: int, pixel_threshold: int) -> tuple[Optional[bytes], int, bool]:
    """Convert a character to its hexadecimal representation.
    
    Args:
        character (str): The character to convert.
        char_size (int): The size of the text (height of the matrix).
        font_path (str): The path to the font file.
        font_offset (tuple[int, int]): The (x, y) offset for the font.
        font_size (int): The font size to use for rendering.
        pixel_threshold (int): Threshold for converting grayscale to binary.
        
    Returns:
        tuple: (hex_string, char_width, is_emoji)
    """

    if is_emoji(character):
        try:
            # Download and load emoji image from Twemoji
            img = get_emoji_image(character, size=char_size)
            
            if img is None:
                logger.error(f"Failed to get emoji image for {character}")
                return None, 0, False
            
            # Convert to JPEG format
            buffer = BytesIO()
            # Save JPEG with Adobe format (used by official app)
            # subsampling=0 means 4:4:4 (best quality, preserves colors)
            # quality=95 for high quality
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
            
            return jpeg_bytes, char_size, True
        except Exception as e:
            logger.error(f"Error rendering emoji {character}: {e}")
            return None, 0, False
    else:
        try:
            # Generate image with dynamic width
            # First, create a temporary large image to measure text in grayscale
            temp_img = Image.new('L', (100, char_size), 0)
            temp_draw = ImageDraw.Draw(temp_img)
            font_obj = ImageFont.truetype(font_path, font_size)
            
            # Get text bounding box
            bbox = temp_draw.textbbox((0, 0), character, font=font_obj)
            text_width = bbox[2] - bbox[0]

            # Clamp text_width between min and max values to prevent crash
            if char_size == 32:
                min_width = 9
                max_width = 16
            else:
                min_width = 1
                max_width = 16
            text_width = int(max(min_width, min(text_width, max_width)))

            # Create final image in grayscale mode for pixel-perfect rendering
            img = Image.new('L', (int(text_width), int(char_size)), 0)
            d = ImageDraw.Draw(img)
            
            # Draw text in white (255) for pixel-perfect rendering
            d.text(font_offset, character, fill=255, font=font_obj)

            # Apply threshold for pixel-perfect conversion
            def apply_threshold(pixel):
                return 255 if pixel > pixel_threshold else 0

            img = img.point(apply_threshold, mode='L')

            bytes_data, width = _charimg_to_hex_string(img)
            return bytes_data, width, False
        except Exception as e:
            logger.error(f"Error occurred while converting character to hex: {e}")
            return None, 0, False


def _encode_text(text: str, text_size: int, color: str, font_path: str, font_offset: tuple[int, int], font_size: int, pixel_threshold: int) -> bytes:
    """Encode text to be displayed on the device.

    Returns raw bytes. Each character block is composed as:
      0x80 + color(3 bytes) + char_width(1 byte) + matrix_height(1 byte) + frame_bytes...

    Args:
        text (str): The text to encode.
        matrix_height (int): The height of the LED matrix.
        color (str): The color in hex format (e.g., 'ffffff').
        font (str): The font name to use.
        font_offset (tuple[int, int]): The (x, y) offset for the font.

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

    # Build each character block
    for char in text:
        char_bytes, char_width, is_emoji_flag = _char_to_hex(char, text_size, font_path, font_offset, font_size, pixel_threshold)
        if not char_bytes:
            continue

        if not is_emoji_flag:
            # Apply byte-level transformations
            char_bytes = _logic_reverse_bits_order_bytes(char_bytes)

        # Build bytes for this character
        if text_size == 32:
            if is_emoji_flag:
                result += bytes([0x09])  # Char 32x32, used for emoji
                result += len(char_bytes).to_bytes(2, byteorder='little')  # Payload size
                result += bytes([0x00])  # Reserved
            elif char_width <= 16:
                result += bytes([0x02])  # Char 32x16
                result += color_bytes
            elif char_width <= 32:
                result += bytes([0x90])  # Char 32x32
                result += color_bytes
                result += bytes([char_width & 0xFF])
                result += bytes([text_size & 0xFF])
            else:
                raise ValueError(f"Character width {char_width} exceeds maximum for 32px height.")
        else:  # text_size == 16
            if is_emoji_flag:
                # Emoji JPEG format: 0x08 + payload_size(2 bytes LE) + 0x00
                result += bytes([0x08])  # Special type for emoji
                result += len(char_bytes).to_bytes(2, byteorder='little')  # Payload size
                result += bytes([0x00])  # Reserved
            elif char_width <= 8:
                result += bytes([0x00])  # Char 16x8
                result += color_bytes
            elif char_width <= 16:
                result += bytes([0x80])  # Char 16x16
                result += color_bytes
                result += bytes([char_width & 0xFF])
                result += bytes([text_size & 0xFF])
            else:
                raise ValueError(f"Character width {char_width} exceeds maximum for 16px height.")
        
        result += char_bytes

    return bytes(result)


# Main function to send text command
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
            char_height = device_info.height
            logger.debug(f"Auto-detected matrix height from device: {char_height}")
        else:
            char_height = 16  # Default fallback
            logger.warning("Using default matrix height: 16")
    
    char_height = int(char_height)
    
    # Get metrics for this character height
    metrics = font_config.get_metrics(char_height)
    font_size = metrics["font_size"]
    font_offset = metrics["offset"]
    pixel_threshold = metrics["pixel_threshold"]
    
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

    characters_bytes = _encode_text(
        text, 
        char_height, 
        color, 
        font_config.path,
        font_offset,
        font_size,
        pixel_threshold
    )
    
    # number_of_characters: single byte
    data_payload = bytes([len(text)]) + properties + characters_bytes

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
        frame_header += bytes([0x00])                                  # Reserved
        frame_header += bytes([int(save_slot) & 0xFF])                 # save_slot
        
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
