import pytest

from pypixelcolor.commands.set_fun_mode import set_pixel


def test_set_pixel_accepts_six_hex_digits():
    data = set_pixel(1, 2, "ff0000").windows[0].data
    assert list(data) == [10, 0, 5, 1, 0, 255, 0, 0, 1, 2]


@pytest.mark.parametrize("color", [
    "ff0000ff",  # 8 chars: was silently truncated
    "fff",
    "gggggg",
    0xff0000,    # was TypeError from len()
    None,        # was TypeError from len()
])
def test_set_pixel_rejects_invalid_colors(color):
    with pytest.raises(ValueError, match="6-character hexadecimal"):
        set_pixel(1, 2, color)
