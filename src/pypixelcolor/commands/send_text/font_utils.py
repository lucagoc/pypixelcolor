# -*- coding: utf-8 -*-
"""Font configuration and device-specific utilities."""

import os
from typing import Union
from logging import getLogger

from ...lib.device_info import DeviceInfo
from ...lib.font_config import FontConfig, BUILTIN_FONTS
from ...lib.font_calibrator import download_google_font, download_font_url

logger = getLogger(__name__)


def resolve_font_config(font: Union[str, FontConfig]) -> FontConfig:
    """Resolve a font specification to a FontConfig object.
    
    Args:
        font: Either a built-in font name (str), a 'google:<name>' font, a URL,
              a file path (str), or a FontConfig object
        
    Returns:
        FontConfig object
        
    Raises:
        ValueError: If font argument type is invalid or Google Font cannot be fetched
        FileNotFoundError: If font file is not found
    """
    if isinstance(font, FontConfig):
        return font
    
    if not isinstance(font, str):
        raise ValueError(f"Font must be a string or FontConfig, got {type(font)}")
    
    # Try built-in fonts first (UNIFONT)
    if font.upper() in BUILTIN_FONTS:
        return BUILTIN_FONTS[font.upper()]

    # Google Fonts prefix (e.g. 'google:Silkscreen' or 'google:Press Start 2P')
    if font.lower().startswith("google:"):
        family = font[7:].strip()
        local_path = download_google_font(family)
        return FontConfig.from_file(str(local_path), name=family)

    # HTTP/HTTPS URL
    if font.startswith("http://") or font.startswith("https://"):
        local_path = download_font_url(font)
        return FontConfig.from_file(str(local_path))
    
    # Try loading as file path
    if os.path.exists(font):
        return FontConfig.from_file(font)
    
    raise FileNotFoundError(f"Font '{font}' not found. Available built-in: UNIFONT. For Google Fonts, use 'google:<name>'.")


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
