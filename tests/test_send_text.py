#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pytest to validate `send_text` payloads defined in `tests/resources/send_text.json`."""
import sys
from pathlib import Path

# Ensure project src is importable
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from .lib.test_send_text import lib_test_send_text_payloads

def test_send_text_16():
    lib_test_send_text_payloads("send_text_16.json")
    
def test_send_text_16_VCR_OSD_MONO():
    lib_test_send_text_payloads("send_text_16_VCR_OSD_MONO.json")    

# def test_send_text_24():
#     lib_test_send_text_payloads("send_text_24.json")
    
def test_send_text_32():    
    lib_test_send_text_payloads("send_text_32.json")