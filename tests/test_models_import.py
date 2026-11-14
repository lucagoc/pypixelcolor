# -*- coding: utf-8 -*-
"""Tests verifying public models and enums are cleanly importable."""

def test_import_from_root_package():
    """Verify models are importable directly from pypixelcolor."""
    from pypixelcolor import (
        TextAnimation,
        TimerAction,
        ScheduleDay,
        ResizeMethod,
        FontConfig,
        DeviceInfo,
        Client,
        AsyncClient,
    )

    assert TextAnimation.STATIC == 0
    assert TimerAction.START == 1
    assert ScheduleDay.SAT == 0x80
    assert ResizeMethod.CROP.value == "crop"


def test_import_from_models_module():
    """Verify models are importable from pypixelcolor.models."""
    from pypixelcolor.models import (
        TextAnimation,
        TimerAction,
        ScheduleDay,
        ResizeMethod,
        FontConfig,
        DeviceInfo,
    )

    assert TextAnimation.BLINK == 5
    assert TextAnimation.FADE == 6
    assert TextAnimation.SNOWFLAKE == 7
    assert TextAnimation.LASER == 8
    assert TimerAction.STOP == 0
    assert ScheduleDay.MON == 0x02
    assert ResizeMethod.FIT.value == "fit"
