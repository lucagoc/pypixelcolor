import logging
import pytest

from pypixelcolor.commands.send_text.color_utils import (
    has_color_tags,
    strip_color_tags,
    parse_colored_text,
)
from pypixelcolor.commands.send_text.encoding import encode_text
from pypixelcolor.commands.send_text.models import RenderContext
from pypixelcolor.commands.send_text import send_text
from pypixelcolor.lib.font_config import FontConfig


def test_has_color_tags():
    assert has_color_tags("[#ff0000]Hello[/]") is True
    assert has_color_tags("[00ff00]World[/#]") is True
    assert has_color_tags("[#123456]Test[/color]") is True
    assert has_color_tags("Simple text without tags") is False
    assert has_color_tags("[not_a_color]text") is False


def test_strip_color_tags():
    assert strip_color_tags("[#ff0000]Hello[/] [#00ff00]World[/]") == "Hello World"
    assert strip_color_tags("[ff0000]A[00ff00]B[/]C[/]") == "ABC"
    assert strip_color_tags("Plain text") == "Plain text"


def test_parse_colored_text():
    # Plain text gets default color
    text, colors = parse_colored_text("Hello", default_color="ffffff")
    assert text == "Hello"
    assert colors == ["ffffff"] * 5

    # Sequential tags
    text, colors = parse_colored_text("[#ff0000]AB[/][#00ff00]CD[/]", default_color="ffffff")
    assert text == "ABCD"
    assert colors == ["ff0000", "ff0000", "00ff00", "00ff00"]

    # Text before, inside, and after tags
    text, colors = parse_colored_text("A[#ff0000]B[/]C", default_color="000000")
    assert text == "ABC"
    assert colors == ["000000", "ff0000", "000000"]

    # Nested tags
    text, colors = parse_colored_text("[#ff0000]A[#00ff00]B[/]C[/]", default_color="ffffff")
    assert text == "ABC"
    assert colors == ["ff0000", "00ff00", "ff0000"]

    # Hex without # prefix and lowercase/uppercase normalization
    text, colors = parse_colored_text("[FF0000]X[/]", default_color="112233")
    assert text == "X"
    assert colors == ["ff0000"]


def test_encode_text_with_char_colors():
    font = FontConfig.builtin("UNIFONT")
    metrics = font.get_metrics(16)
    context = RenderContext(
        char_height=16,
        font_path=font.path,
        font_size=int(metrics["font_size"]),
        font_offset=tuple(metrics["offset"]),
        pixel_threshold=int(metrics["pixel_threshold"]),
    )

    char_colors = ["ff0000", "00ff00"]
    encoded = encode_text(
        text="AB",
        color_bytes=bytes.fromhex("ffffff"),
        context=context,
        reverse=False,
        char_colors=char_colors,
    )

    # Each character block starts with 1B opcode + 3B RGB color + bitmap
    # First char 'A' should have color ff0000
    assert encoded[1:4] == bytes.fromhex("ff0000")

    # Second char starts after first char block (for 16px half-width, 1 + 3 + 16 = 20 bytes)
    assert encoded[21:24] == bytes.fromhex("00ff00")


def test_encode_text_with_char_colors_reversed():
    font = FontConfig.builtin("UNIFONT")
    metrics = font.get_metrics(16)
    context = RenderContext(
        char_height=16,
        font_path=font.path,
        font_size=int(metrics["font_size"]),
        font_offset=tuple(metrics["offset"]),
        pixel_threshold=int(metrics["pixel_threshold"]),
    )

    char_colors = ["ff0000", "00ff00"]  # 'A': red, 'B': green
    encoded = encode_text(
        text="AB",
        color_bytes=bytes.fromhex("ffffff"),
        context=context,
        reverse=True,
        char_colors=char_colors,
    )

    # When reversed, 'B' is first, so first block has green color
    assert encoded[1:4] == bytes.fromhex("00ff00")
    # 'A' is second, so second block has red color
    assert encoded[21:24] == bytes.fromhex("ff0000")


def test_send_text_end_to_end_per_char_colors():
    plan = send_text(
        text="[#ff0000]A[/][#00ff00]B[/]",
        char_height=16,
        var_width=False,
    )
    assert plan.id == "send_text"
    window = next(iter(plan.windows))
    # Frame header: 2B len prefix + [00 01 00] [4B size] [4B crc] [00 save_slot] = 15 bytes
    # Data payload starts at index 15:
    data_payload = window.data[15:]
    num_chars = data_payload[0]
    assert num_chars == 2

    # Character blocks start after 1B num_chars + 13B properties = index 14 of data_payload
    char_block_1 = data_payload[14:]
    assert char_block_1[1:4] == bytes.fromhex("ff0000")

    char_block_2 = data_payload[14 + 20:]
    assert char_block_2[1:4] == bytes.fromhex("00ff00")


def test_send_text_var_width_warns_and_ignores_tags(caplog):
    with caplog.at_level(logging.WARNING):
        plan = send_text(
            text="[#ff0000]Hello[/]",
            char_height=16,
            var_width=True,
        )
    assert "Color tags are not supported with var_width and will be ignored." in caplog.text
    assert plan.id == "send_text"
