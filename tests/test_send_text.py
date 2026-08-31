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


def test_send_text_manual_overrides(mock_device, monkeypatch):
    """Verify manual font parameter overrides are accepted and correctly passed."""
    import pypixelcolor.commands.send_text as send_text_mod

    captured_params = {}
    orig_encode = send_text_mod.encode_text

    def mock_encode(*args, **kwargs):
        captured_params["offset"] = args[4]
        captured_params["font_size"] = args[5]
        captured_params["pixel_threshold"] = args[6]
        return orig_encode(*args, **kwargs)

    monkeypatch.setattr(send_text_mod, "encode_text", mock_encode)

    # 1. Native types override
    send_text(
        text="Test",
        device_info=mock_device,
        font_size=14,
        font_offset=(0, 2),
        pixel_threshold=80,
        var_width=False,
    )
    assert captured_params["font_size"] == 14
    assert captured_params["offset"] == (0, 2)
    assert captured_params["pixel_threshold"] == 80

    # 2. String representation override (from CLI / WebSocket)
    send_text(
        text="Test",
        device_info=mock_device,
        font_size="18",
        font_offset="1,3",
        pixel_threshold="45",
        var_width="false",
    )
    assert captured_params["font_size"] == 18
    assert captured_params["offset"] == (1, 3)
    assert captured_params["pixel_threshold"] == 45


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


def test_send_text_var_width_from_config(mock_device):
    """Verify send_text uses var_width from font configuration without command arg."""
    from pypixelcolor.lib.font_config import UNIFONT_PATH

    fc = FontConfig(
        name="CUSTOM_VAR",
        path=UNIFONT_PATH,
        metrics={
            16: {"font_size": 16, "offset": (0, 0), "pixel_threshold": 30, "var_width": True}
        }
    )

    plan = send_text("HELLO", font=fc, device_info=mock_device)
    assert hasattr(plan, "windows")
    windows = list(plan.windows)
    assert len(windows) > 0


def test_send_text_var_width_override(mock_device, monkeypatch):
    """Verify send_text var_width argument overrides font configuration."""
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

    # Font has var_width=False, but command passes var_width=True
    fc_fixed = FontConfig(
        name="FIXED",
        path=UNIFONT_PATH,
        metrics={16: {"font_size": 16, "offset": (0, 0), "pixel_threshold": 30, "var_width": False}}
    )
    called_funcs.clear()
    send_text("HI", font=fc_fixed, var_width=True, device_info=mock_device)
    assert called_funcs == ["chunked"]

    # Font has var_width=True, but command passes var_width=False
    fc_var = FontConfig(
        name="VAR",
        path=UNIFONT_PATH,
        metrics={16: {"font_size": 16, "offset": (0, 0), "pixel_threshold": 30, "var_width": True}}
    )
    called_funcs.clear()
    send_text("HI", font=fc_var, var_width=False, device_info=mock_device)
    assert called_funcs == ["standard"]

    # Test string boolean parsing (e.g. from CLI "true" / "false")
    called_funcs.clear()
    send_text("HI", font=fc_fixed, var_width="true", device_info=mock_device)
    assert called_funcs == ["chunked"]

    called_funcs.clear()
    send_text("HI", font=fc_var, var_width="false", device_info=mock_device)
    assert called_funcs == ["standard"]
