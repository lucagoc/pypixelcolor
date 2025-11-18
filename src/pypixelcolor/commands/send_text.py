# -*- coding: utf-8 -*-

# Imports
import os
import binascii
from PIL import Image, ImageDraw, ImageFont
from logging import getLogger
from typing import Optional, Union

# Locals
from ..lib.transport.send_plan import single_window_plan
from ..lib.device_info import DeviceInfo
from ..fonts.font_enum import Font, FONT_METRICS

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

# Helper function to encode text

def get_font_path(font_name: str) -> str:
    """Get the path to the font directory or file."""
    # Get the base directory where fonts are stored (pypixelcolor/fonts)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    fonts_dir = os.path.join(base_dir, "fonts")
    
    try:
        font = Font.from_str(font_name)
        return os.path.join(fonts_dir, font.value + ".ttf")
    except:
        pass
    
    # Check if ttf file exists
    font_file = os.path.join(fonts_dir, f"{font_name}.ttf")
    if os.path.isfile(font_file):
        return font_file
    
    # Check if folder exists
    font_folder = os.path.join(fonts_dir, font_name)
    if os.path.isdir(font_folder):
        return font_folder
    
    # Return default font path
    default_font = os.path.join(fonts_dir, Font.CUSONG.value + ".ttf")
    logger.warning(f"Font '{font_name}' not found. Using default font at {default_font}.")
    return default_font


def charimg_to_hex_string(img: Image.Image) -> tuple[bytes, int]:
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


def char_to_hex(character: str, char_size:int, font_offset: tuple[int, int], font: str, font_size: int) -> tuple[Optional[bytes], int]:
    """
    Convert a character to its hexadecimal representation.
    
    Args:
        character (str): The character to convert.
        text_size (int): The size of the text (height of the matrix).
        font_offset (tuple[int, int]): The (x, y) offset for the font.
        font (str): The font name to use.
        
    Returns:
        tuple: (hex_string, char_width)
    """
    font_path = get_font_path(font)

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
        # Values tested on 16px height device
        # Might be different for 20px or 24px devices
        min_width = 1
        max_width = 16
        text_width = int(max(min_width, min(text_width, max_width)))

        # Create final image in grayscale mode for pixel-perfect rendering
        img = Image.new('L', (int(text_width), int(char_size)), 0)
        d = ImageDraw.Draw(img)
        
        # Draw text in white (255) for pixel-perfect rendering
        d.text(font_offset, character, fill=255, font=font_obj)

        # Determine pixel threshold from FONT_METRICS for the selected font/size
        pixel_threshold = 100
        try:
            font_enum = Font.from_str(font) if not isinstance(font, Font) else font
            font_metrics = FONT_METRICS.get(font_enum, {})
            pixel_threshold = font_metrics.get(int(char_size), {}).get("pixel_threshold", pixel_threshold)
        except Exception:
            # Fallback to default threshold if anything goes wrong
            pass

        # Apply threshold for pixel-perfect conversion
        def apply_threshold(pixel):
            return 255 if pixel > pixel_threshold else 0

        img = img.point(apply_threshold, mode='L')

        return charimg_to_hex_string(img)
    except Exception as e:
        logger.error(f"Error occurred while converting character to hex: {e}")
        return None, 0


def _encode_text(text: str, text_size: int, color: str, font: str, font_offset: tuple[int, int], font_size: int) -> bytes:
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
        char_bytes, char_width = char_to_hex(char, text_size, font=font, font_offset=font_offset, font_size=font_size)
        if not char_bytes:
            continue

        # Apply byte-level transformations
        char_bytes = _logic_reverse_bits_order_bytes(char_bytes)

        # Build bytes for this character
        if char_width <= 8:
            result += bytes([0x00]) # 8px width, 16px height
        elif text_size >= 32:
            result += bytes([0x02]) # 32 height
        else:
            result += bytes([0x80]) # 16px width, 8px height
        result += color_bytes
        if char_width > 8 and text_size < 32:
            result += bytes([char_width & 0xFF])
            result += bytes([text_size & 0xFF])
        result += char_bytes

    return bytes(result)


# Main function to send text command
def send_text(text: str,
              rainbow_mode: int = 0,
              animation: int = 0,
              save_slot: int = 0,
              speed: int = 80,
              color: str = "ffffff",
              font: Union[Font, str] = Font.CUSONG,
              font_size: Optional[int] = None,
              font_offset: Optional[Optional[tuple[int, int]]] = None,
              char_height: Optional[int] = None,
              device_info: Optional[DeviceInfo] = None
              ):
    """
    Send a text to the device with configurable parameters.

    Args:
        text (str): The text to send.
        rainbow_mode (int, optional): Rainbow mode (0-9). Defaults to 0.
        animation (int, optional): Animation type (0-7, except 3 and 4). Defaults to 0.
        save_slot (int, optional): Save slot (1-10). Defaults to 1.
        speed (int, optional): Animation speed (0-100). Defaults to 80.
        color (str, optional): Text color in hex. Defaults to "ffffff".
        font (str, optional): Font name. Defaults to "default".
        font_offset_x (int, optional): Font X offset. Defaults to 0.
        font_offset_y (int, optional): Font Y offset. Defaults to 0.
        text_size (int, optional): Text size. Auto-detected from device_info if not specified.
        device_info (DeviceInfo, optional): Device information (injected automatically by DeviceSession).

    Returns:
        bytes: Encoded command to send to the device.

    Raises:
        ValueError: If an invalid animation is selected or parameters are out of range.
    """
    
    # Auto-detect matrix_height from device_info if available
    if char_height is None:
        if device_info is not None:
            char_height = device_info.height
            logger.debug(f"Auto-detected matrix height from device: {char_height}")
        else:
            char_height = 16  # Default fallback
            logger.warning("Using default matrix height: 16")
        
        # Get offset from FONT_METRICS if available
        try:
            font_enum = Font.from_str(font) if not isinstance(font, Font) else font
            font_metrics = FONT_METRICS.get(font_enum, {})
            if char_height in font_metrics:
                font_offset = font_metrics[char_height]["offset"]
                font_size = font_metrics[char_height]["font_size"]
        except Exception:
            pass
        
    # Normalize font_offset to two integers (x, y)
    try:
        font_offset_x, font_offset_y = font_offset if font_offset is not None else (0, 0)
        font_offset_x = int(font_offset_x)
        font_offset_y = int(font_offset_y)
    except Exception:
        raise ValueError("font_offset must be a tuple of two integers (x, y)")
    char_height = int(char_height)
    if font_size is None:
        font_size = char_height
    
    # properties: 3 fixed bytes + animation + speed + rainbow + 3 bytes color + 4 zero bytes
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
        (len(text), 1, 100, "Text length"),
        (char_height, 1, 128, "Char height"),
    ]
    for param, min_val, max_val, name in checks:
        if not (min_val <= param <= max_val):
            raise ValueError(f"{name} must be between {min_val} and {max_val} (got {param})")
    
    # Normalize font: accept either FontName or str for backward compatibility
    if isinstance(font, Font):
        font_str = font.value
    else:
        font_str = str(font)

    # Disable unsupported animations (bootloop)
    if int(animation) == 3 or int(animation) == 4:
        raise ValueError("Invalid animation for text display")

    #---------------- BUILD PAYLOAD ----------------#

    ########################
    #        HEADER        #
    ########################
    
    header = bytearray()

    # Determine if the font entry declares 16-bit metrics.
    font_16bit = False
    font_enum = Font.from_str(font_str) if not isinstance(font, Font) else font
    font_metrics = FONT_METRICS.get(font_enum, {})
    if char_height in font_metrics:
        font_16bit = font_metrics[char_height]["is_16bit"]
                
    # Magic formulas
    if char_height <= 16:
        header1_val = 29 + len(text) * (20 + (18 if font_16bit else 0))
        header3_val = 14 + len(text) * (20 + (18 if font_16bit else 0))
    elif char_height <= 20:
        header1_val = 0x1D + len(text) * (0x04 + char_height * (0x1 if char_height <= 16 else 0x2)) + 0x01
        header3_val = 0x0E + len(text) * (0x04 + char_height * (0x1 if char_height <= 16 else 0x2)) + 0x01
    elif char_height <= 24:
        header1_val = 0x1D + len(text) * (0x04 + char_height * (0x1 if char_height <= 16 else 0x2)) + 0x02
        header3_val = 0x0E + len(text) * (0x04 + char_height * (0x1 if char_height <= 16 else 0x2)) + 0x02
    else:
        header1_val = 29 + len(text) * 68
        header3_val = 14 + len(text) * 68
    
    header += header1_val.to_bytes(2, byteorder="little")
    header += bytes([
        0x00, # Reserved
        0x01, # Reserved
        0x00  # Reserved
    ])
    header += header3_val.to_bytes(2, byteorder="little")
    header += bytes([
        0x00,   # Reserved 
        0x00    # Reserved
    ])

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
    properties += bytes([
        0x00,   # Reserved
        0x00,   # Reserved
        0x00,   # Reserved
        0x00    # Reserved
    ])

    #########################
    #       CHARACTERS      #
    #########################

    characters_bytes = _encode_text(
        text, 
        char_height, 
        color, 
        font_str, 
        (font_offset_x, font_offset_y),
        font_size
    )
    
    # number_of_characters: single byte
    data_payload = bytes([len(text)]) + properties + characters_bytes

    #########################
    #        CHECKSUM       #
    #########################

    crc = binascii.crc32(data_payload) & 0xFFFFFFFF

    #########################
    #     FINAL PAYLOAD     #
    #########################

    # Assemble final payload
    final_payload = bytearray()
    final_payload += bytes(header)                                  # header
    final_payload += crc.to_bytes(4, byteorder="little")            # checksum
    final_payload += bytes([0x00])                                  # Reserved
    final_payload += bytes([int(save_slot) & 0xFF])                 # save_slot
    final_payload += data_payload                                   # num_chars + properties + characters

    # Debug
    logger.debug("final_payload (hex): %s", bytes(final_payload).hex())

    return single_window_plan("send_text", bytes(final_payload))
