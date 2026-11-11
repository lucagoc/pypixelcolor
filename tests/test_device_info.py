# -*- coding: utf-8 -*-
"""Tests for `0x8005` firmware-version parsing."""

import pytest

from pypixelcolor.lib.device_info import parse_device_info, parse_hw_info


# Captured from the real B.K. Light 64x16 panel (device byte 131).
REAL_8001 = bytes.fromhex("0b 00 01 80 83 00 00 00 00 01 00")
REAL_8005 = bytes.fromhex("08 00 05 80 0e 02 07 04")


def test_parse_real_device_info():
    info = parse_device_info(REAL_8001)

    assert info.device_type == 131
    assert info.led_type == 3
    assert (info.width, info.height) == (64, 16)
    assert info.password_flag == 0
    # Versions are not in the 0x8001 reply.
    assert info.mcu_version == "unknown"
    assert info.wifi_version == "unknown"


def test_parse_real_hw_info():
    assert parse_hw_info(REAL_8005) == ("14.02", "7.04")


def test_parse_hw_info_zero_pads_minor():
    reply = bytes([8, 0, 5, 0x80, 2, 0, 3, 9])
    assert parse_hw_info(reply) == ("2.00", "3.09")


def test_parse_device_info_rejects_short_response():
    with pytest.raises(ValueError):
        parse_device_info(b"\x08\x00\x01\x80")


def test_parse_hw_info_rejects_wrong_reply():
    # A 5-byte ACK must not be mistaken for a version reply.
    with pytest.raises(ValueError):
        parse_hw_info(bytes([5, 0, 2, 0, 1]))
    with pytest.raises(ValueError):
        parse_hw_info(b"\x08\x00\x05\x80")
