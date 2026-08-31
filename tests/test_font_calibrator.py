# -*- coding: utf-8 -*-
"""Tests for font calibration and disk cache."""

import os
from pypixelcolor.lib.font_calibrator import (
    calculate_font_metrics, get_cached_metrics, get_cache_dir
)
from pypixelcolor.lib.font_config import UNIFONT_PATH


def test_calculate_font_metrics():
    """Verify metrics calculation produces valid structure for UNIFONT."""
    metrics_16 = calculate_font_metrics(UNIFONT_PATH, 16)
    assert 14 <= metrics_16["font_size"] <= 20
    assert isinstance(metrics_16["offset"], tuple)
    assert len(metrics_16["offset"]) == 2
    assert 30 <= metrics_16["pixel_threshold"] <= 180

    metrics_32 = calculate_font_metrics(UNIFONT_PATH, 32)
    assert 30 <= metrics_32["font_size"] <= 40
    assert metrics_32["font_size"] > metrics_16["font_size"]


def test_get_cached_metrics():
    """Verify metrics caching to disk works and returns expected heights."""
    metrics = get_cached_metrics(UNIFONT_PATH, heights=(16, 24, 32))
    assert 16 in metrics
    assert 24 in metrics
    assert 32 in metrics

    cache_file = get_cache_dir() / "font_metrics.json"
    assert cache_file.exists()

    # Second call should read from cache file without error
    metrics_second = get_cached_metrics(UNIFONT_PATH, heights=(16, 24, 32))
    assert metrics == metrics_second


def test_silkscreen_calibration():
    """Verify fonts like Silkscreen calibrate with valid size and no clipping."""
    from pypixelcolor.lib.font_calibrator import get_fonts_cache_dir
    silkscreen_path = get_fonts_cache_dir() / "Silkscreen.ttf"
    if silkscreen_path.exists():
        metrics = calculate_font_metrics(str(silkscreen_path), 16)
        assert 12 <= metrics["font_size"] <= 20
        assert isinstance(metrics["offset"], tuple)
