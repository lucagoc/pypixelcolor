# -*- coding: utf-8 -*-
"""Tests for DeviceSession.connect() cleanup on partial failures."""

import asyncio
from unittest import mock

import pytest

from pypixelcolor.lib.device_info import DeviceInfo
from pypixelcolor.lib.device_session import DeviceSession

MAC = "D0:BB:AD:65:91:10"


class FakeBleakClient:
    def __init__(self, address, disconnected_callback=None):
        self.address = address
        self.disconnected_callback = disconnected_callback
        self.is_connected = False
        self.connect_calls = 0
        self.disconnect_calls = 0
        self.notify_started = 0

    async def connect(self):
        self.connect_calls += 1
        self.is_connected = True

    async def start_notify(self, uuid, handler):
        self.notify_started += 1

    async def stop_notify(self, uuid):
        pass

    async def disconnect(self):
        self.disconnect_calls += 1
        self.is_connected = False


def _session():
    # Skip the BLE pre-scan: these tests only exercise connect cleanup.
    return DeviceSession(MAC, connect_scan_timeout=0)


def _patch_client(fake):
    return mock.patch(
        "pypixelcolor.lib.device_session.BleakClient",
        return_value=fake,
    )


def test_connect_closes_client_when_device_info_fails():
    session = _session()
    fake = FakeBleakClient(MAC)

    async def fail_fetch(self):
        raise RuntimeError("device info unavailable")

    with _patch_client(fake), mock.patch.object(
        DeviceSession, "_fetch_device_info", fail_fetch
    ):
        with pytest.raises(RuntimeError, match="device info unavailable"):
            asyncio.run(session.connect())

    # The BLE client must be closed and the session reset (no half-open link).
    assert fake.disconnect_calls == 1
    assert fake.is_connected is False
    assert session._connected is False
    assert session._client is None
    assert session._ack_mgr is None
    assert session._device_info is None


def test_connect_closes_client_when_bleak_connect_fails():
    session = _session()
    fake = FakeBleakClient(MAC)

    async def fail_connect():
        raise RuntimeError("gatt connect failed")

    with _patch_client(fake):
        fake.connect = fail_connect
        with pytest.raises(RuntimeError, match="gatt connect failed"):
            asyncio.run(session.connect())

    # _connected was never set, but the client object still gets released.
    assert fake.disconnect_calls == 1
    assert session._connected is False
    assert session._client is None


def test_connect_keeps_client_open_on_success():
    session = _session()
    fake = FakeBleakClient(MAC)
    info = DeviceInfo(
        device_type=131,
        mcu_version="1.0",
        wifi_version="1.0",
        width=64,
        height=16,
        has_wifi=False,
        password_flag=255,
        led_type=3,
    )

    async def ok_fetch(self):
        self._device_info = info

    with _patch_client(fake), mock.patch.object(
        DeviceSession, "_fetch_device_info", ok_fetch
    ):
        result = asyncio.run(session.connect())

    assert result is info
    assert fake.disconnect_calls == 0
    assert session._connected is True
    assert session._client is fake

    asyncio.run(session.disconnect())
    assert fake.disconnect_calls == 1
    assert session._connected is False
    assert session._client is None
    assert session._device_info is None


def test_disconnect_is_idempotent_and_warns_when_not_connected():
    session = _session()
    asyncio.run(session.disconnect())  # no client: must not raise
    assert session._connected is False
    assert session._client is None
