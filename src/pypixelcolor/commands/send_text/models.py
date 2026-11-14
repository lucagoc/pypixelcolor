# -*- coding: utf-8 -*-
"""Data models for text encoding and animation."""

from enum import Enum, IntEnum
from dataclasses import dataclass
from typing import Union


class TextAnimation(IntEnum):
    """Text animation types for LED matrix displays.

    Values:
        STATIC (0): Fixed text without animation.
        SCROLL_LEFT (1): Continuous scroll from right to left.
        SCROLL_RIGHT (2): Continuous scroll from left to right.
        SCROLL_UP (3): Scroll upwards (32x32 devices only).
        SCROLL_DOWN (4): Scroll downwards (32x32 devices only).
        BLINK (5): Fast blinking text effect.
        FADE (6): Smooth blinking / breathing effect with continuous attenuation.
        SNOWFLAKE (7): Snowflake falling effect.
        LASER (8): Laser beam sweep, column by column (right to left).
    """

    STATIC = 0
    SCROLL_LEFT = 1
    SCROLL_RIGHT = 2
    SCROLL_UP = 3
    SCROLL_DOWN = 4
    BLINK = 5
    FADE = 6
    SNOWFLAKE = 7
    LASER = 8


def parse_animation(animation: Union[TextAnimation, str, int]) -> TextAnimation:
    """Parse and validate an animation argument into a TextAnimation enum.

    Args:
        animation: TextAnimation enum instance, string name (e.g. 'scroll_left', 'blink'),
                   or integer opcode (0-8).

    Returns:
        TextAnimation instance.

    Raises:
        ValueError: If animation is invalid or unrecognized.
    """
    if isinstance(animation, TextAnimation):
        return animation

    if isinstance(animation, str):
        cleaned = animation.strip().upper().replace("-", "_")
        if cleaned in TextAnimation.__members__:
            return TextAnimation[cleaned]
        if cleaned.isdigit():
            animation = int(cleaned)

    if isinstance(animation, int) and not isinstance(animation, bool):
        try:
            return TextAnimation(animation)
        except ValueError:
            pass

    valid_names = ", ".join(m.lower() for m in TextAnimation.__members__)
    raise ValueError(
        f"Invalid animation: {animation!r}. Expected integer (0-8) or name ({valid_names})."
    )


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


@dataclass(frozen=True)
class RenderContext:
    """Parameters required to render glyphs and text chunks."""
    char_height: int
    font_path: str
    font_size: int
    font_offset: tuple[int, int]
    pixel_threshold: int

