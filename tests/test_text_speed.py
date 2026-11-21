# -*- coding: utf-8 -*-
"""Tests for the text_speed command.

text_speed / send_text speed parameter (0-100).
"""

import pytest

from pypixelcolor.commands import COMMANDS
from pypixelcolor.commands.text_speed import text_speed
from pypixelcolor.commands.send_text import send_text


def test_text_speed_registration():
    """text_speed is registered in COMMANDS dict."""
    assert "text_speed" in COMMANDS
    assert COMMANDS["text_speed"] is text_speed


def test_text_speed_default_speed():
    """Default speed is 80."""
    plan = text_speed("hello")
    assert plan.id == "send_text"
    assert plan.windows[0].data is not None


def test_text_speed_custom_speed():
    """Custom speed is forwarded to send_text."""
    plan = text_speed("hello", speed=5)
    assert plan.id == "send_text"
    assert plan.windows[0].data is not None


def test_text_speed_forward_kwargs():
    """Forwarded kwargs (color, bg_color, ...) reach send_text."""
    plan = text_speed("hello", color="#ffffff", bg_color="ff0000")
    assert plan.id == "send_text"
    assert plan.windows[0].data is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
