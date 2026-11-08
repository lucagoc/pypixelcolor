# -*- coding: utf-8 -*-
"""Tests for the pre-scan connect gate (PanelNotAdvertisingError).

The panel only accepts a BLE connection while it advertises; a phone
already connected to the panel stops the advertisements. The gate
turns a blind GATT connect into a fast, actionable error.
"""

import asyncio
from unittest import mock

import pytest

from pypixelcolor import PanelNotAdvertisingError
from pypixelcolor.lib.device_session import (
    DEFAULT_CONNECT_SCAN_TIMEOUT,
    DeviceSession,
)

MAC = "D0:BB:AD:65:91:10"


def _run(coro):
    return asyncio.run(coro)


def test_default_scan_window_is_15s():
    """The scan window is a bounded maximum (the scan returns on first hit)."""
    assert DEFAULT_CONNECT_SCAN_TIMEOUT == 15.0
    assert DeviceSession(MAC)._connect_scan_timeout == 15.0


def test_pre_scan_raises_actionable_error_when_not_seen():
    session = DeviceSession(MAC)
    with mock.patch(
        "pypixelcolor.lib.device_session.BleakScanner.find_device_by_address",
        mock.AsyncMock(return_value=None),
    ):
        with pytest.raises(PanelNotAdvertisingError) as excinfo:
            _run(session._pre_scan())

    msg = str(excinfo.value)
    assert MAC in msg
    # The user must be told what to do about the missing advertisement.
    assert "iPixel app" in msg
    assert "not seen" in msg


def test_pre_scan_returns_when_device_seen():
    session = DeviceSession(MAC)
    # bleak 3.x BLEDevice has no rssi attribute — log line must tolerate it.
    device = mock.MagicMock()
    device.rssi = None
    device.name = "B.K. Light"
    with mock.patch(
        "pypixelcolor.lib.device_session.BleakScanner.find_device_by_address",
        mock.AsyncMock(return_value=device),
    ):
        _run(session._pre_scan())  # no raise


def test_pre_scan_skipped_with_zero_timeout():
    """connect_scan_timeout=0 restores the old direct-connect behaviour."""
    session = DeviceSession(MAC, connect_scan_timeout=0)
    with mock.patch(
        "pypixelcolor.lib.device_session.BleakScanner.find_device_by_address",
        mock.AsyncMock(return_value=None),
    ) as find:
        _run(session._pre_scan())
    find.assert_not_awaited()
