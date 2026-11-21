# -*- coding: utf-8 -*-
"""Validation tests for the date handling of set_clock_mode.

The docstring documents DD/MM/YYYY, while the wire format stores a 2-digit
year. Both forms must be accepted and normalised to the same wire bytes.
"""

from datetime import datetime

import pytest

from pypixelcolor.commands.set_clock_mode import set_clock_mode


def _data(plan):
    return plan.windows[0].data


def test_accepts_four_digit_year():
    data = _data(set_clock_mode(date="11/11/2026"))
    # header [len, 0, cmd=6, type=1], style, 24h, show_date, year, month, day, weekday
    assert list(data[7:11]) == [26, 11, 11, 3]  # 2026-11-11 is a Wednesday


def test_accepts_two_digit_year():
    assert _data(set_clock_mode(date="11/11/26")) == _data(
        set_clock_mode(date="11/11/2026"))


def test_default_uses_current_year_as_two_digits():
    data = _data(set_clock_mode())
    assert data[7] == datetime.now().year % 100


@pytest.mark.parametrize("date", [
    "11/11/1999",  # outside the panel's 2000..2099 wire range
    "32/01/2026",  # impossible day
    "29/02/2025",  # not a leap year
    "11/13/2026",  # impossible month
    "2026-11-11",  # wrong separator
    "11/11",       # missing year
])
def test_rejects_invalid_dates(date):
    with pytest.raises(ValueError):
        set_clock_mode(date=date)
