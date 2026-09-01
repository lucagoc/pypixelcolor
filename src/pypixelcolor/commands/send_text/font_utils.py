# -*- coding: utf-8 -*-
"""Font configuration and device-specific utilities."""

import os
import re
from typing import Union
from logging import getLogger
from pathlib import Path

from ...lib.device_info import DeviceInfo
from ...lib.font_config import FontConfig, BUILTIN_FONTS
from ...lib.font_calibrator import download_google_font, get_fonts_cache_dir

logger = getLogger(__name__)


def resolve_font_config(font: Union[str, FontConfig]) -> FontConfig:
    """Resolve a font specification to a FontConfig object.
    
    Args:
        font: Either a built-in font name (str), a Google Font name (e.g. 'Silkscreen'),
              a local file path (str), or a FontConfig object.
        
    Returns:
        FontConfig object
        
    Raises:
        ValueError: If font argument type is invalid
        FileNotFoundError: If font cannot be found locally or on online.
    """
    if isinstance(font, FontConfig):
        return font
    
    if not isinstance(font, str):
        raise ValueError(f"Font must be a string or FontConfig, got {type(font)}")

    cleaned_font = font.strip()

    # 1. Try built-in fonts first (UNIFONT)
    if cleaned_font.upper() in BUILTIN_FONTS:
        return BUILTIN_FONTS[cleaned_font.upper()]

    # 2. Try loading as direct file path
    if os.path.exists(cleaned_font):
        return FontConfig.from_file(cleaned_font)

    # 4. Check if already cached in fonts cache dir
    fonts_dir = get_fonts_cache_dir()
    safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', cleaned_font)
    for ext in (".ttf", ".otf"):
        cached_candidate = fonts_dir / f"{safe_name}{ext}"
        if cached_candidate.exists() and cached_candidate.stat().st_size > 0:
            return FontConfig.from_file(str(cached_candidate), name=cleaned_font)

    # 5. Automatically search and download from Google Fonts if not found locally
    try:
        local_path = download_google_font(cleaned_font)
        return FontConfig.from_file(str(local_path), name=cleaned_font)
    except Exception as e:
        logger.debug(f"Font '{cleaned_font}' not found on Google Fonts: {e}")

    raise FileNotFoundError(
        f"Font '{font}' not found. Available built-in: UNIFONT."
    )


def get_char_height_from_device(device_info: DeviceInfo) -> int:
    """Map device dimensions to appropriate character height.

    Args:
        device_info (DeviceInfo): Device information with width and height.
        
    Returns:
        int: The recommended character height (16 or 32).
    """
    if device_info.height <= 20:
        return 16
    else:
        return device_info.height
