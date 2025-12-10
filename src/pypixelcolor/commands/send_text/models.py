# -*- coding: utf-8 -*-
"""Data models for text encoding."""

from enum import Enum
from dataclasses import dataclass


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
