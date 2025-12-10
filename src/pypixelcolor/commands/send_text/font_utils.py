# -*- coding: utf-8 -*-
"""Font configuration and device-specific utilities."""

import os
from typing import Union
from logging import getLogger

from ...lib.device_info import DeviceInfo
from ...lib.font_config import FontConfig, BUILTIN_FONTS

logger = getLogger(__name__)


def resolve_font_config(font: Union[str, FontConfig]) -> FontConfig:
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


def get_char_height_from_device(device_info: DeviceInfo) -> int:
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
