# -*- coding: utf-8 -*-
"""User configuration management for permanent font metrics.

Stored in ~/.config/pypixelcolor/fonts.json (following XDG Base Directory specification).
"""

import json
import os
from pathlib import Path
from typing import Optional

from .font_calibrator import _get_font_cache_key


def get_user_config_dir() -> Path:
    """Return the user configuration directory (e.g. ~/.config/pypixelcolor)."""
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config:
        config_dir = Path(xdg_config) / "pypixelcolor"
    else:
        config_dir = Path.home() / ".config" / "pypixelcolor"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_user_fonts_config_path() -> Path:
    """Return path to user fonts.json configuration file."""
    return get_user_config_dir() / "fonts.json"


def load_user_fonts_config() -> dict[str, dict]:
    """Load user fonts.json configuration file or return empty dict if not found."""
    config_file = get_user_fonts_config_path()
    if not config_file.exists():
        return {}
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def get_user_font_metrics(font_path: str, font_name: Optional[str] = None) -> Optional[dict[int, dict]]:
    """Retrieve permanent user-configured metrics for a font if present.
    
    Args:
        font_path: Path to the font file.
        font_name: Optional font name for cache key resolution.
        
    Returns:
        Dict mapping height (int) to metrics dict {font_size, offset, pixel_threshold},
        or None if not configured by user.
    """
    config_data = load_user_fonts_config()
    if not config_data:
        return None

    resolved_name = font_name or Path(font_path).stem
    cache_key = _get_font_cache_key(font_path, resolved_name)
    font_entry = config_data.get(cache_key)
    if not font_entry:
        return None

    result = {}
    for k, v in font_entry.items():
        if k.isdigit() and isinstance(v, dict):
            h = int(k)
            result[h] = {
                "font_size": v["font_size"],
                "offset": tuple(v["offset"]),
                "pixel_threshold": v["pixel_threshold"],
                "var_width": bool(v.get("var_width", False)),
            }
    return result if result else None


def save_user_font_metrics(font_path: str, font_name: str, metrics: dict[int, dict]) -> None:
    """Save user-configured metrics permanently to ~/.config/pypixelcolor/fonts.json.
    
    Args:
        font_path: Path to the font file.
        font_name: Display name of the font.
        metrics: Dict mapping height (int) to metrics dict {font_size, offset, pixel_threshold, var_width}.
    """
    config_dir = get_user_config_dir()
    config_file = get_user_fonts_config_path()
    config_data = load_user_fonts_config()

    cache_key = _get_font_cache_key(font_path, font_name)
    font_entry = config_data.get(cache_key, {})

    for h, m in metrics.items():
        font_entry[str(h)] = {
            "font_size": m["font_size"],
            "offset": list(m["offset"]),
            "pixel_threshold": m["pixel_threshold"],
            "var_width": bool(m.get("var_width", False)),
        }

    config_data[cache_key] = font_entry

    temp_file = config_file.with_suffix(".tmp")
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=2)
    temp_file.replace(config_file)
