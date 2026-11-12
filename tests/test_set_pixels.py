# -*- coding: utf-8 -*-
"""Tests for the set_pixels / set_pixel paint commands.

The paint frame is a single 5-byte-header frame followed by the color
and one (x, y) pair per point. A single point reduces to the classic
10-byte set_pixel frame. The frame is fire-and-forget (requires_ack=False):
the panel does not ACK paint writes, verified on panel.
"""

import pytest

from pypixelcolor.lib.device_info import DeviceInfo
from pypixelcolor.commands.set_fun_mode import MirrorMode, set_pixel, set_pixels
from pypixelcolor.commands import COMMANDS


def _frame(plan):
    """Return the raw bytes of the single window of a plan."""
    windows = list(plan.windows)
    assert len(windows) == 1
    return windows[0].data


def test_set_pixels_single_point_matches_set_pixel_frame():
    """A one-point frame is byte-identical to the classic set_pixel frame."""
    multi = _frame(set_pixels([(3, 4)], "ff0000"))
    single = _frame(set_pixel(3, 4, "ff0000"))
    # [len, 0, 5, 1, 0, R, G, B, x, y]
    assert multi == bytes([10, 0, 5, 1, 0, 0xFF, 0x00, 0x00, 3, 4])
    assert multi == single


def test_set_pixels_multi_point_frame():
    """Verify the frame layout for multiple points (verified on panel)."""
    pts = [(x, 8) for x in range(10, 32, 3)]
    data = _frame(set_pixels(pts, "00ff00"))
    # Header
    assert len(data) == 8 + 2 * len(pts)
    assert data[0] == len(data)      # length byte
    assert data[1:5] == bytes([0, 5, 1, 0])  # reserved, cmd, type, option
    assert data[5:8] == bytes([0x00, 0xFF, 0x00])  # R, G, B
    # Points, in order
    coords = data[8:]
    for i, (x, y) in enumerate(pts):
        assert coords[2 * i] == x
        assert coords[2 * i + 1] == y


def test_set_pixels_requires_ack_is_false():
    """Paint frames are fire-and-forget (no ACK expected)."""
    plan = set_pixels([(0, 0), (1, 1)], "ffffff")
    windows = list(plan.windows)
    assert windows[0].requires_ack is False
    assert plan.id == "set_pixels"


def test_set_pixel_delegates_to_set_pixels():
    """set_pixel is a one-point specialization of set_pixels."""
    assert _frame(set_pixel(10, 5, "00ff00")) == _frame(set_pixels([(10, 5)], "00ff00"))


def test_set_pixels_color_validation():
    """PC-1: only a 6-char hex string is a valid color; anything else raises."""
    # Valid
    _frame(set_pixels([(0, 0)], "a1b2c3"))
    _frame(set_pixels([(0, 0)], "FF0000"))
    # Invalid: 8-char (was silently accepted before the fix)
    with pytest.raises(ValueError, match="hexadecimal"):
        set_pixels([(0, 0)], "ff0000ff")
    # Invalid: too short
    with pytest.raises(ValueError, match="hexadecimal"):
        set_pixels([(0, 0)], "fff")
    # Invalid: non-hex
    with pytest.raises(ValueError, match="hexadecimal"):
        set_pixels([(0, 0)], "xyzxyz")
    # Invalid: non-string (was TypeError before the fix)
    with pytest.raises(ValueError, match="hexadecimal"):
        set_pixels([(0, 0)], 0xFF0000)
    with pytest.raises(ValueError, match="hexadecimal"):
        set_pixels([(0, 0)], b"ff0000")


def test_set_pixels_empty_points_raises():
    with pytest.raises(ValueError, match="At least one point"):
        set_pixels([], "ff0000")


def test_set_pixels_too_many_points_raises():
    """The frame length is a single byte, so the point count is capped."""
    with pytest.raises(ValueError, match="123"):
        set_pixels([(i, 0) for i in range(124)], "ff0000")
    # At the limit, the frame length byte is still valid (8 + 2*123 = 254).
    data = _frame(set_pixels([(i, 0) for i in range(123)], "ff0000"))
    assert len(data) == 254


def test_set_pixels_device_info_validation():
    """Coordinates are checked against the panel when device_info is given."""
    info = DeviceInfo(
        device_type=131, mcu_version="14.02", wifi_version="7.04",
        width=64, height=16, has_wifi=False, password_flag=255, led_type=3,
    )
    # In range
    _frame(set_pixels([(63, 15)], "ff0000", device_info=info))
    # Out of range
    with pytest.raises(ValueError, match="coordinates range"):
        set_pixels([(64, 0)], "ff0000", device_info=info)
    with pytest.raises(ValueError, match="coordinates range"):
        set_pixels([(0, 16)], "ff0000", device_info=info)


def test_set_pixels_registered():
    """Both commands are registered for dynamic client methods."""
    assert "set_pixel" in COMMANDS
    assert "set_pixels" in COMMANDS


def test_set_pixels_mirror_option_byte():
    """Mirror mode goes into the option byte (HW-verified: panel paints each
    point plus its mirror image on the opposite side)."""
    assert _frame(set_pixels([(4, 2)], "00ff00"))[4] == 0
    assert _frame(set_pixels([(4, 2)], "00ff00", mirror="horizontal"))[4] == 1
    assert _frame(set_pixels([(4, 2)], "00ff00", mirror="vertical"))[4] == 2
    assert _frame(set_pixels([(4, 2)], "00ff00", mirror=MirrorMode.HORIZONTAL))[4] == 1
    assert _frame(set_pixels([(4, 2)], "00ff00", mirror=1))[4] == 1


def test_set_pixels_mirror_keeps_frame_layout():
    """Mirroring is done by the panel; the frame only carries N points."""
    pts = [(6, 3), (8, 5), (10, 7)]
    data = _frame(set_pixels(pts, "00ff00", mirror="horizontal"))
    assert len(data) == 8 + 2 * len(pts)
    assert data[0] == len(data)
    assert data[4] == 1
    assert data[8:] == bytes([6, 3, 8, 5, 10, 7])


def test_set_pixels_mirror_invalid_raises():
    for bad in ("both", "diagonal", 3, 4, True):
        with pytest.raises(ValueError, match="mirror mode"):
            set_pixels([(0, 0)], "ff0000", mirror=bad)


def test_set_pixel_mirror_passthrough():
    assert _frame(set_pixel(4, 2, "00ff00", mirror="vertical")) == \
        _frame(set_pixels([(4, 2)], "00ff00", mirror="vertical"))
