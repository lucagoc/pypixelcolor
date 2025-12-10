# -*- coding: utf-8 -*-
"""Image processing utilities for text rendering."""

from typing import Optional
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from logging import getLogger

from ...lib.emoji_manager import get_emoji_image

logger = getLogger(__name__)


def apply_pixel_threshold(img: Image.Image, threshold: int) -> Image.Image:
    """Apply threshold to convert grayscale image to binary.
    
    Args:
        img (Image.Image): Input grayscale image.
        threshold (int): Pixel value threshold (0-255).
    
    Returns:
        Image.Image: Binary image (black/white only).
    """
    def _threshold_func(p: int) -> int:
        return 255 if p > threshold else 0
    
    return img.point(_threshold_func, mode='L')


def create_text_image(text: str, height: int, font_path: str, 
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
    img = apply_pixel_threshold(img, pixel_threshold)
    
    # Get dimensions
    bbox = draw.textbbox((0, 0), text, font=font_obj)
    text_width = bbox[2] - bbox[0]
    
    return img, {'bbox': bbox, 'width': text_width, 'draw': draw, 'font': font_obj}


def render_text_segment_to_chunks(text: str, height: int, font_path: str, 
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
    img, meta = create_text_image(text, height, font_path, offset, font_size, pixel_threshold)
    # Crop to actual text width with padding
    img = img.crop((0, 0, meta['width'] + 4, height))
    return split_image_into_chunks(img, chunk_width)


def encode_char_img(img: Image.Image) -> bytes:
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


def emoji_to_hex(emoji: str, emoji_height: int) -> Optional[bytes]:
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


def char_to_hex(character: str, char_height: int, font_path: str, font_offset: tuple[int, int], font_size: int, pixel_threshold: int) -> Optional[bytes]:
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
        img = apply_pixel_threshold(img, pixel_threshold)

        bytes_data = encode_char_img(img)
        return bytes_data
    except Exception as e:
        logger.error(f"Error occurred while converting character to hex: {e}")
        return None


def split_image_into_chunks(img: Image.Image, chunk_width: int) -> list[Image.Image]:
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
