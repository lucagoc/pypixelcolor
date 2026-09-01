# -*- coding: utf-8 -*-
"""Color utilities for parsing and handling inline text color tags."""

import re


# Pattern matching opening tags like [#ff0000] or [ff0000], and closing tags like [/], [/#], [/color]
COLOR_TOKEN_PATTERN = re.compile(
    r'\[#?([0-9a-fA-F]{6})\]|(\[/(?:color|#)?\])'
)


def parse_hex_color(color: str, name: str = "Color") -> bytes:
    """Validate and convert a 6-character hex string to 3 RGB bytes.

    Args:
        color (str): Hex color string, e.g. 'ffffff' or '#ffffff'.
        name (str): Field name for descriptive error message.

    Returns:
        bytes: 3 bytes RGB representation.

    Raises:
        ValueError: If color string is invalid or not 3 bytes.
    """
    clean = color.lstrip("#")
    try:
        color_bytes = bytes.fromhex(clean)
    except Exception:
        raise ValueError(f"Invalid {name.lower()} hex: {color}")
    if len(color_bytes) != 3:
        raise ValueError(f"{name} must be 3 bytes (6 hex chars), e.g. 'ffffff'")
    return color_bytes


def has_color_tags(text: str) -> bool:
    """Check if text contains any inline color tags."""
    return bool(COLOR_TOKEN_PATTERN.search(text))


def strip_color_tags(text: str) -> str:
    """Strip all inline color tags from text, returning raw characters."""
    return COLOR_TOKEN_PATTERN.sub('', text)


def parse_colored_text(raw_text: str, default_color: str = "ffffff") -> tuple[str, list[str]]:
    """Parse inline color tags from text into clean text and per-character colors.

    Args:
        raw_text (str): Text containing optional tags, e.g. '[#ff0000]Hello[/] World'.
        default_color (str): Base hex color to use outside tags (e.g. 'ffffff').

    Returns:
        tuple[str, list[str]]: (clean_text, char_colors) where char_colors
        has one 6-character hex color string for each character in clean_text.
    """
    clean_default_color = default_color.lower().lstrip("#")
    if len(clean_default_color) != 6:
        clean_default_color = "ffffff"

    color_stack = [clean_default_color]
    clean_chars: list[str] = []
    char_colors: list[str] = []

    last_idx = 0
    for match in COLOR_TOKEN_PATTERN.finditer(raw_text):
        start, end = match.span()

        # Add characters between tags with current active color
        if start > last_idx:
            chunk = raw_text[last_idx:start]
            current_color = color_stack[-1]
            for c in chunk:
                clean_chars.append(c)
                char_colors.append(current_color)

        color_hex, close_tag = match.groups()
        if color_hex is not None:
            color_stack.append(color_hex.lower())
        elif close_tag is not None:
            if len(color_stack) > 1:
                color_stack.pop()

        last_idx = end

    # Add remaining characters after last tag
    if last_idx < len(raw_text):
        chunk = raw_text[last_idx:]
        current_color = color_stack[-1]
        for c in chunk:
            clean_chars.append(c)
            char_colors.append(current_color)

    return "".join(clean_chars), char_colors
