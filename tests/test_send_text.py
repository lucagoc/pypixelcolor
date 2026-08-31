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
    """Verify FontConfig.builtin loads UNIFONT with valid metrics."""
    font = FontConfig.builtin("UNIFONT")
    assert font.name == "UNIFONT"
    assert 16 in font.metrics
    assert 32 in font.metrics
    metrics_16 = font.get_metrics(16)
    assert "font_size" in metrics_16
    assert "offset" in metrics_16
    assert "pixel_threshold" in metrics_16


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


def test_send_text_manual_overrides(mock_device):
    """Verify manual font parameter overrides are accepted."""
    plan = send_text(
        text="Test",
        device_info=mock_device,
        font_size=14,
        font_offset=(0, 1),
        pixel_threshold=80
    )
    assert len(list(plan.windows)) > 0


def test_resolve_google_font(monkeypatch):
    """Verify resolve_font_config handles google: prefix."""
    from pypixelcolor.commands.send_text.font_utils import resolve_font_config
    from pypixelcolor.lib.font_config import UNIFONT_PATH
    from pathlib import Path

    # Mock download_google_font to return UNIFONT_PATH
    monkeypatch.setattr(
        "pypixelcolor.commands.send_text.font_utils.download_google_font",
        lambda family: Path(UNIFONT_PATH)
    )

    fc = resolve_font_config("google:Silkscreen")
    assert fc.name == "Silkscreen"
    assert 16 in fc.metrics
