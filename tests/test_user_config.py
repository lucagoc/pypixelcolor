# -*- coding: utf-8 -*-
"""Tests for user configuration in ~/.config/pypixelcolor/fonts.json."""

import json
from pathlib import Path
from pypixelcolor.lib.font_config import UNIFONT_PATH
from pypixelcolor.lib.user_config import (
    get_user_fonts_config_path,
    load_user_fonts_config,
    save_user_font_metrics,
    get_user_font_metrics,
)
from pypixelcolor.lib.font_calibrator import get_cached_metrics


def test_user_config_save_and_load(tmp_path, monkeypatch):
    """Verify user font metrics can be saved and loaded accurately."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    metrics_to_save = {
        16: {"font_size": 18, "offset": (0, -2), "pixel_threshold": 85, "var_width": True},
        24: {"font_size": 25, "offset": (0, -3), "pixel_threshold": 90, "var_width": False},
    }

    save_user_font_metrics(UNIFONT_PATH, "UNIFONT", metrics_to_save)

    config_path = get_user_fonts_config_path()
    assert config_path.exists()

    with open(config_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    # Check key starts with UNIFONT_
    key = list(raw_data.keys())[0]
    assert key.startswith("UNIFONT_")
    assert "16" in raw_data[key]
    assert raw_data[key]["16"]["font_size"] == 18
    assert raw_data[key]["16"]["var_width"] is True
    assert raw_data[key]["24"]["var_width"] is False

    # Check get_user_font_metrics
    retrieved = get_user_font_metrics(UNIFONT_PATH, "UNIFONT")
    assert retrieved is not None
    assert retrieved[16]["font_size"] == 18
    assert retrieved[16]["offset"] == (0, -2)
    assert retrieved[16]["pixel_threshold"] == 85
    assert retrieved[16]["var_width"] is True
    assert retrieved[24]["var_width"] is False


def test_user_config_overrides_cache(tmp_path, monkeypatch):
    """Verify metrics in user config override cache / auto-calibration."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    custom_metrics = {
        16: {"font_size": 19, "offset": (0, -5), "pixel_threshold": 120}
    }
    save_user_font_metrics(UNIFONT_PATH, "UNIFONT", custom_metrics)

    metrics = get_cached_metrics(UNIFONT_PATH, heights=(16, 24, 32), font_name="UNIFONT")
    assert metrics[16]["font_size"] == 19
    assert metrics[16]["offset"] == (0, -5)
    assert metrics[16]["pixel_threshold"] == 120
    # Height 24 should still be resolved via cache or auto-calc
    assert 24 in metrics
