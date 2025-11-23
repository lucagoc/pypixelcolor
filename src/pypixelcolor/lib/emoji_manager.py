# -*- coding: utf-8 -*-

"""
Emoji Manager - Downloads and caches Twemoji images
"""

import urllib.request
from pathlib import Path
from typing import Optional
from logging import getLogger
from PIL import Image
from io import BytesIO

logger = getLogger(__name__)

# Twemoji CDN base URL (using latest version)
TWEMOJI_BASE_URL = "https://cdn.jsdelivr.net/gh/twitter/twemoji@latest/assets/72x72/"

# Cache directory for downloaded emojis
CACHE_DIR = Path.home() / ".cache" / "pypixelcolor" / "emojis"


def get_emoji_codepoint(char: str) -> str:
    """Convert an emoji character to its Unicode codepoint representation.
    
    Args:
        char: The emoji character
        
    Returns:
        Codepoint string in the format used by Twemoji (e.g., "1f600")
    """
    # Get codepoints for all characters (handles multi-codepoint emojis)
    codepoints = []
    for c in char:
        code = ord(c)
        # Filter out variation selectors (U+FE0F) and zero-width joiners (U+200D)
        if code not in [0xFE0F]:
            codepoints.append(f"{code:x}")
    
    # Join codepoints with hyphen for multi-codepoint emojis (e.g., flags, skin tones)
    # Keep ZWJ (200d) for sequences like family emojis
    result = "-".join(codepoints)
    return result


def is_emoji(char: str) -> bool:
    """Check if a character is an emoji.
    
    Args:
        char: The character to check
        
    Returns:
        True if the character is an emoji, False otherwise
    """
    if not char:
        return False
    
    code = ord(char[0])
    
    # Check common emoji ranges
    return (
        0x1F600 <= code <= 0x1F64F or  # Emoticons
        0x1F300 <= code <= 0x1F5FF or  # Misc Symbols and Pictographs
        0x1F680 <= code <= 0x1F6FF or  # Transport and Map
        0x1F1E6 <= code <= 0x1F1FF or  # Regional indicator symbols (flags)
        0x2600 <= code <= 0x26FF or    # Misc symbols
        0x2700 <= code <= 0x27BF or    # Dingbats
        0x1F900 <= code <= 0x1F9FF or  # Supplemental Symbols and Pictographs
        0x1FA00 <= code <= 0x1FA6F or  # Extended-A
        0x1FA70 <= code <= 0x1FAFF or  # Extended-B
        0x231A <= code <= 0x231B or    # Watch, hourglass
        0x23E9 <= code <= 0x23F3 or    # Media controls
        0x25AA <= code <= 0x25AB or    # Squares
        0x25B6 <= code <= 0x25C0 or    # Triangles
        0x25FB <= code <= 0x25FE or    # Squares
        0x2934 <= code <= 0x2935 or    # Arrows
        0x3030 <= code <= 0x3030 or    # Wavy dash
        0x303D <= code <= 0x303D or    # Part alternation mark
        0x3297 <= code <= 0x3299       # CJK unified ideographs
    )


def download_emoji(char: str) -> Optional[Image.Image]:
    """Download an emoji image from Twemoji CDN.
    
    Args:
        char: The emoji character
        
    Returns:
        PIL Image object, or None if download fails
    """
    # Ensure cache directory exists
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    # Get codepoint for the emoji
    codepoint = get_emoji_codepoint(char)
    
    # Check if already cached
    cache_path = CACHE_DIR / f"{codepoint}.png"
    if cache_path.exists():
        logger.debug(f"Loading cached emoji: {codepoint}")
        try:
            return Image.open(cache_path)
        except Exception as e:
            logger.warning(f"Failed to load cached emoji {codepoint}: {e}")
            # Remove corrupted cache file
            cache_path.unlink(missing_ok=True)
    
    # Download from Twemoji CDN
    url = f"{TWEMOJI_BASE_URL}{codepoint}.png"
    logger.debug(f"Downloading emoji from: {url}")
    
    try:
        # Download the image
        with urllib.request.urlopen(url, timeout=5) as response:
            image_data = response.read()
        
        # Load image from bytes
        img = Image.open(BytesIO(image_data))
        
        # Save to cache
        img.save(cache_path, "PNG")
        logger.debug(f"Cached emoji: {codepoint}")
        
        return img
    
    except Exception as e:
        logger.error(f"Failed to download emoji {char} ({codepoint}): {e}")
        return None


def get_emoji_image(char: str, size: int = 16) -> Optional[Image.Image]:
    """Get an emoji image, downloading if necessary and resizing to specified size.
    
    Args:
        char: The emoji character
        size: Desired size in pixels (width and height)
        
    Returns:
        PIL Image object (RGB mode) at the requested size, or None if unavailable
    """
    # Download or load from cache
    img = download_emoji(char)
    if img is None:
        return None
    
    # Convert palette images with transparency to RGBA to avoid PIL warning
    if img.mode == 'P' and 'transparency' in img.info:
        img = img.convert('RGBA')
    
    # Resize to requested size with high quality
    img = img.resize((size, size), Image.Resampling.LANCZOS)
    
    # Convert RGBA to RGB with black background
    if img.mode == 'RGBA':
        background = Image.new('RGB', (size, size), (0, 0, 0))
        background.paste(img, mask=img.split()[3])  # Use alpha channel as mask
        img = background
    elif img.mode != 'RGB':
        img = img.convert('RGB')
    
    return img


def clear_emoji_cache():
    """Clear the emoji cache directory."""
    import shutil
    if CACHE_DIR.exists():
        shutil.rmtree(CACHE_DIR)
        logger.info("Emoji cache cleared")
