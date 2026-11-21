# -*- coding: utf-8 -*-
"""Tests for send_text command and font calibration."""

import pytest
from pypixelcolor.commands.send_text import send_text
from pypixelcolor.lib.font_config import FontConfig, list_fonts
from pypixelcolor.lib.device_info import DeviceInfo


@pytest.fixture
def mock_device():
    """Create a mock 64x64 DeviceInfo."""
    return DeviceInfo(
        device_type=130,
        mcu_version="unknown",
        wifi_version="unknown",
        width=64,
        height=64,
        has_wifi=False,
        password_flag=255,
        led_type=0,
    )


def test_list_fonts():
    """Verify built-in font list contains UNIFONT."""
    fonts = list_fonts()
    assert "UNIFONT" in fonts


def test_builtin_font_config():
    """Verify FontConfig.builtin loads UNIFONT with valid default configuration."""
    font = FontConfig.builtin("UNIFONT")
    assert font.name == "UNIFONT"
    assert font.path.endswith("unifont.otf")
    assert font.offset == (0, 0)
    assert font.pixel_threshold == 128
    assert font.var_width is False


def test_unknown_font_raises():
    """Verify requesting an unknown font raises FileNotFoundError or ValueError."""
    with pytest.raises((FileNotFoundError, ValueError)):
        send_text(text="Test", font="UNKNOWN_NONEXISTENT_FONT", char_height=16)


def test_send_text_default_unifont(mock_device):
    """Verify send_text works with default UNIFONT font."""
    plan = send_text(text="Hello World", device_info=mock_device)
    assert hasattr(plan, "windows")
    windows = list(plan.windows)
    assert len(windows) > 0
    assert len(windows[0].data) > 0


def test_send_text_multilingual(mock_device):
    """Verify send_text renders multi-language text (Latin, accents, Chinese, Japanese)."""
    text = "Bonjour 世界 こんにちは"
    plan = send_text(text=text, device_info=mock_device)
    windows = list(plan.windows)
    assert len(windows) > 0
    assert len(windows[0].data) > 0


def test_font_config_from_string():
    """Verify FontConfig.from_string parses names, paths, and key-value pairs."""
    from pypixelcolor.lib.font_config import UNIFONT_PATH

    # 1. Built-in font name or empty
    fc1 = FontConfig.from_string("UNIFONT")
    assert fc1.name == "UNIFONT"
    assert fc1.var_width is False

    fc1_empty = FontConfig.from_string("")
    assert fc1_empty.name == "UNIFONT"

    # 2. File path
    fc2 = FontConfig.from_string(UNIFONT_PATH)
    assert fc2.path == UNIFONT_PATH
    assert fc2.var_width is False

    # 3. Direct options without path or name (defaults to UNIFONT)
    fc3 = FontConfig.from_string("var_width=true,font_size=16")
    assert fc3.name == "UNIFONT"
    assert fc3.var_width is True
    assert fc3.font_size == 16

    # 4. Path with key-value overrides
    fc4 = FontConfig.from_string(f"path={UNIFONT_PATH},font_size=14,offset=0;2,pixel_threshold=80,var_width=true")
    assert fc4.path == UNIFONT_PATH
    assert fc4.font_size == 14
    assert fc4.offset == (0, 2)
    assert fc4.pixel_threshold == 80
    assert fc4.var_width is True



def test_send_text_key_value_font_string(mock_device, monkeypatch):
    """Verify send_text with key-value font string passes parameters correctly."""
    from pypixelcolor.lib.font_config import UNIFONT_PATH
    import pypixelcolor.commands.send_text as send_text_mod

    captured_params = {}
    orig_encode = send_text_mod.encode_text

    def mock_encode(text, color_bytes, context, *args, **kwargs):
        captured_params["offset"] = context.font_offset
        captured_params["font_size"] = context.font_size
        captured_params["pixel_threshold"] = context.pixel_threshold
        return orig_encode(text, color_bytes, context, *args, **kwargs)

    monkeypatch.setattr(send_text_mod, "encode_text", mock_encode)

    send_text(
        text="Test",
        device_info=mock_device,
        font=f"path={UNIFONT_PATH},font_size=18,offset=1:3,pixel_threshold=45",
    )
    assert captured_params["font_size"] == 18
    assert captured_params["offset"] == (1, 3)
    assert captured_params["pixel_threshold"] == 45


def test_send_text_var_width_from_config(mock_device):
    """Verify send_text uses var_width from font configuration."""
    from pypixelcolor.lib.font_config import UNIFONT_PATH

    fc = FontConfig(
        name="CUSTOM_VAR",
        path=UNIFONT_PATH,
        var_width=True,
    )

    plan = send_text("HELLO", font=fc, device_info=mock_device)
    assert hasattr(plan, "windows")
    windows = list(plan.windows)
    assert len(windows) > 0


def test_send_text_var_width_from_string(mock_device, monkeypatch):
    """Verify send_text switches to chunked encoding when var_width=true in font string."""
    from pypixelcolor.lib.font_config import UNIFONT_PATH
    import pypixelcolor.commands.send_text as send_text_mod

    called_funcs = []
    orig_chunked = send_text_mod.encode_text_chunked
    orig_standard = send_text_mod.encode_text

    def mock_chunked(*args, **kwargs):
        called_funcs.append("chunked")
        return orig_chunked(*args, **kwargs)

    def mock_standard(*args, **kwargs):
        called_funcs.append("standard")
        return orig_standard(*args, **kwargs)

    monkeypatch.setattr(send_text_mod, "encode_text_chunked", mock_chunked)
    monkeypatch.setattr(send_text_mod, "encode_text", mock_standard)

    # Key-value string with var_width=true
    called_funcs.clear()
    send_text("HI", font=f"path={UNIFONT_PATH},var_width=true", device_info=mock_device)
    assert called_funcs == ["chunked"]

    # Key-value string with var_width=false
    called_funcs.clear()
    send_text("HI", font=f"path={UNIFONT_PATH},var_width=false", device_info=mock_device)
    assert called_funcs == ["standard"]



def test_send_text_animation_parameters(mock_device):
    """Verify animation accepts TextAnimation enum, string names, and integers."""
    from pypixelcolor.models import TextAnimation

    # 1. Enum instances
    plan_enum = send_text("Hello", animation=TextAnimation.SCROLL_LEFT, device_info=mock_device)
    assert len(list(plan_enum.windows)) > 0

    # 2. String names (case-insensitive)
    plan_str = send_text("Hello", animation="scroll_left", device_info=mock_device)
    assert len(list(plan_str.windows)) > 0

    plan_blink = send_text("Hello", animation="blink", device_info=mock_device)
    assert len(list(plan_blink.windows)) > 0

    plan_static = send_text("Hello", animation="STATIC", device_info=mock_device)
    assert len(list(plan_static.windows)) > 0

    # 3. Direct integers
    plan_int = send_text("Hello", animation=1, device_info=mock_device)
    assert len(list(plan_int.windows)) > 0

    # Laser (8) — hardware-verified on a 64x16 panel (2026-11-08):
    # beam pixel sweeps right to left, column by column.
    plan_laser = send_text("Hello", animation=TextAnimation.LASER, device_info=mock_device)
    window = next(iter(plan_laser.windows))
    # Text head: [2 len][3 type][4 option][4 size][4 crc][2 tail][count][0x00 0x01 0x01 anim]...
    assert window.data[19] == 8

    plan_laser_str = send_text("Hello", animation="laser", device_info=mock_device)
    assert len(list(plan_laser_str.windows)) > 0

    # 4. Invalid animation raises ValueError
    with pytest.raises(ValueError, match="Invalid animation"):
        send_text("Hello", animation="nonexistent_animation", device_info=mock_device)

    with pytest.raises(ValueError, match="Invalid animation"):
        send_text("Hello", animation=99, device_info=mock_device)


@pytest.fixture
def mock_device_64x16():
    """Create a mock 64x16 DeviceInfo (B.K. Light, device byte 131)."""
    return DeviceInfo(
        device_type=131,
        mcu_version="unknown",
        wifi_version="unknown",
        width=64,
        height=16,
        has_wifi=False,
        password_flag=0,
        led_type=3,
    )


def test_build_text_properties_high_byte():
    """Byte 0 of the properties head is the high byte of the 16-bit item count."""
    from pypixelcolor.commands.send_text import build_text_properties

    white = bytes([0xFF, 0xFF, 0xFF])
    assert build_text_properties(1, 80, 0, white, num_items=1)[0] == 0x00
    assert build_text_properties(1, 80, 0, white, num_items=256)[0] == 0x01
    # 500 = 0x01F4 -> high 0x01
    assert build_text_properties(1, 80, 0, white, num_items=500)[0] == 0x01


def test_send_text_more_than_255_items(mock_device_64x16):
    """num_items is 16-bit little-endian; 256 items no longer raise.

    Pre-fix, `bytes([num_chars])` raised `ValueError: bytes must be in
    range(0, 256)` for 256+ items. Post-fix the count is split into the
    low byte (first head byte) and the high byte (properties byte 0).
    """
    plan = send_text("a" * 256, device_info=mock_device_64x16)
    window = next(iter(plan.windows))
    # Window layout: [len:2][type:2][option][size:4][crc:4][0x00,slot]
    # then the text head: [count_lo, count_hi, 0x01, 0x01, anim, ...]
    assert window.data[15] == 0  # count low byte
    assert window.data[16] == 1  # count high byte (256 = 0x0100)


def test_send_text_item_count_wire_unchanged_under_256(mock_device_64x16):
    """Below 256 items the head bytes are identical to the old layout."""
    plan = send_text("Hello", device_info=mock_device_64x16)
    window = next(iter(plan.windows))
    assert window.data[15] == 5   # count low byte
    assert window.data[16] == 0   # count high byte (was the fixed 0x00)


