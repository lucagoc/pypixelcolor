# -*- coding: utf-8 -*-
"""Font configuration and device-specific utilities."""

import os
from typing import Union, Optional
from logging import getLogger

from ...lib.device_info import DeviceInfo
from ...lib.font_config import FontConfig, BUILTIN_FONTS

logger = getLogger(__name__)

# Cache of font_path -> set of codepoints the font has a glyph for.
# Loading a font's cmap via fontTools is relatively expensive, so this
# avoids re-parsing the same font file for every character in a string.
_glyph_cache: dict[str, set[int]] = {}


def _load_glyph_set(font_path: str) -> set[int]:
    """Load and cache the set of Unicode codepoints a font has glyphs for."""
    if font_path in _glyph_cache:
        return _glyph_cache[font_path]

    try:
        from fontTools.ttLib import TTFont
        tt = TTFont(font_path, fontNumber=0, lazy=True)
        codepoints = set(tt.getBestCmap().keys())
    except Exception as e:
        # If we can't introspect the font (bad path, unsupported format,
        # fontTools missing, etc.), assume nothing is confirmed-covered
        # rather than raising - callers fall back to "just try to render it".
        logger.warning(f"Could not read glyph coverage for font '{font_path}': {e}")
        codepoints = set()

    _glyph_cache[font_path] = codepoints
    return codepoints


def has_glyph(font_path: str, char: str) -> bool:
    """Check whether a font has a glyph for the given character.

    Args:
        font_path (str): Path to the font file.
        char (str): A single character to check.

    Returns:
        bool: True if the font's cmap includes this character's codepoint.
            Returns True (optimistic) if the font's coverage couldn't be
            determined at all, so callers still attempt to render rather
            than treating an unreadable font as having no characters.
    """
    codepoints = _load_glyph_set(font_path)
    if not codepoints:
        return True
    return ord(char) in codepoints


def resolve_font_for_char(char: str, font_path: str,
                           fallback_font_paths: Optional[list[str]] = None) -> str:
    """Pick the first font (primary, then fallbacks in order) that has a
    glyph for this character.

    A missing glyph doesn't raise or render blank - the font/FreeType
    silently substitutes whatever .notdef glyph it has (often a box or
    near-empty shape), which looks like corrupted output rather than an
    obvious failure. This lets a caller route each character to a font
    that actually supports it.

    Args:
        char (str): The character to render.
        font_path (str): Primary font path.
        fallback_font_paths (list[str], optional): Additional font paths
            to try, in order, if the primary font lacks the glyph.

    Returns:
        str: The font path to use. Falls back to font_path itself (with a
            warning logged) if none of the candidates have the glyph -
            rendering will proceed but may look corrupted for that
            character; this is preferable to failing the whole string.
    """
    if has_glyph(font_path, char):
        return font_path

    for fallback_path in (fallback_font_paths or []):
        if has_glyph(fallback_path, char):
            return fallback_path

    logger.warning(
        f"Character {char!r} (U+{ord(char):04X}) is not covered by the "
        f"selected font or any fallback font; it will render incorrectly."
    )
    return font_path


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

    Args:
        device_info (DeviceInfo): Device information with width and height.

    Returns:
        int: The recommended character height (8, 16, or 32).
    """
    if device_info.height <= 20:
        return 16
    else:
        return device_info.height
