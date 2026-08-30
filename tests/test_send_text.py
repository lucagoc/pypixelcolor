#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pytest to validate `send_text` payloads defined in `tests/resources/send_text.json`."""
import sys
from pathlib import Path

# Ensure project src is importable
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from .lib.test_send_text import lib_test_send_text_payloads

from pypixelcolor.commands.send_text import send_text
from pypixelcolor.lib.device_info import DeviceInfo

def test_send_text_16():
    lib_test_send_text_payloads("send_text_16.json") 

# def test_send_text_24():
#     lib_test_send_text_payloads("send_text_24.json")
    
def test_send_text_32():
    lib_test_send_text_payloads("send_text_32.json")

def test_send_text_wide_characters_structure():
    """Verify wide (16px) and normal (8px) characters structure matches official app capture."""
    dev = DeviceInfo(133, "unknown", "unknown", 64, 20, False, 255, 5)
    plan = send_text("あかさbあ", font="tmp/gnu_unifont/UnifontExMono.ttf", save_slot=6, animation=0, speed=80, color="ffffff", device_info=dev)
    assert len(plan.windows) > 0
    data = plan.windows[0].data
    
    # Header length prefix (193 bytes)
    assert len(data) == 193
    assert int.from_bytes(data[0:2], "little") == 193
    
    # 5 characters in text
    assert data[15] == 5
    
    # Extract blocks: あ (16px, 0x01), か (16px, 0x01), さ (16px, 0x01), b (8px, 0x00), あ (16px, 0x01)
    chars_data = data[29:]
    expected_opcodes = [0x01, 0x01, 0x01, 0x00, 0x01]
    expected_sizes = [36, 36, 36, 20, 36]
    
    pos = 0
    for i, (exp_op, exp_size) in enumerate(zip(expected_opcodes, expected_sizes)):
        op = chars_data[pos]
        assert op == exp_op, f"Char {i}: expected opcode {hex(exp_op)}, got {hex(op)}"
        pos += exp_size
    
    assert pos == len(chars_data)