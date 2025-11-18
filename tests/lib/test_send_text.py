#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pytest to validate `send_text` payloads defined in `tests/resources/send_text.json`."""
import json
import sys
from pathlib import Path

# Ensure project src is importable
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pypixelcolor.commands.send_text import send_text
from pypixelcolor.lib.device_info import DeviceInfo, DEVICE_TYPE_MAP, LED_SIZE_MAP


def lib_test_send_text_payloads(file_name: str):
    resource = Path(__file__).parent.parent / "resources" / file_name
    with resource.open("r", encoding="utf-8") as fh:
        data = json.load(fh)

    for case in data.get("tests", []):
        name = case.get("name", "<unnamed>")
        args = case.get("args", {}) or {}

        # Build DeviceInfo from device_type (if provided) so send_text auto-detects text_size
        device_type = case.get("device_type")
        if device_type is not None:
            led_type = DEVICE_TYPE_MAP.get(device_type, 0)
            width, height = LED_SIZE_MAP.get(led_type, (64, 64))
            device_info = DeviceInfo(
                device_type=int(device_type),
                mcu_version="unknown",
                wifi_version="unknown",
                width=width,
                height=height,
                has_wifi=False,
                password_flag=255,
                led_type=led_type,
            )
        else:
            device_info = None

        # Call the API to build the send plan (pass device_info)
        plan = send_text(device_info=device_info, **args)

        # Basic sanity
        assert hasattr(plan, "windows"), f"{name}: plan has no windows"
        windows = list(plan.windows)
        assert len(windows) > 0, f"{name}: plan.windows is empty"

        # Compare first window data hex with expected value if provided
        expected = case.get("expected_data")
        if expected is not None:
            actual_hex = windows[0].data.hex()
            assert actual_hex == expected, f"{name}: payload mismatch\nactual:   {actual_hex}\nexpected: {expected}"
