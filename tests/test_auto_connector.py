#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for auto-connector and custom clock mode."""
import sys
from pathlib import Path

# Ensure project src is importable
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pypixelcolor.commands.set_clock_mode import set_clock_mode


def test_custom_clock_mode():
    """Test custom clock style 9."""
    print("\n=== Testing Custom Clock Mode (Style 9) ===\n")
    
    # Test default
    result = set_clock_mode(style=9)
    assert result is not None
    print("✓ Custom clock style 9 default test passed")
    
    # Test with colors
    colors = {
        "ffffff": "white",
        "ff0000": "red",
        "00ff00": "green",
        "0000ff": "blue",
        "ffff00": "yellow",
    }
    
    print("\n=== Testing Custom Colors ===\n")
    for color, name in colors.items():
        result = set_clock_mode(style=9, color=color, intensity=80)
        assert result is not None
        print(f"  ✓ {name} ({color})")
    
    # Test intensities
    print("\n=== Testing Intensity Levels ===\n")
    for intensity in [0, 25, 50, 75, 100]:
        result = set_clock_mode(style=9, intensity=intensity)
        assert result is not None
        print(f"  ✓ Intensity {intensity}%")
    
    # Test validation
    print("\n=== Testing Validation ===\n")
    try:
        set_clock_mode(style=10)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"✓ Invalid style validation: {e}")
    
    try:
        set_clock_mode(style=9, color="gggggg")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"✓ Invalid color validation: {e}")
    
    try:
        set_clock_mode(style=9, intensity=150)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"✓ Invalid intensity validation: {e}")
    
    print("\n" + "="*60)
    print("  ✓ All tests passed!")
    print("="*60 + "\n")


if __name__ == "__main__":
    test_custom_clock_mode()