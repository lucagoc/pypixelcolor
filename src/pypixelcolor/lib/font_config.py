# -*- coding: utf-8 -*-
"""Font configuration and management."""

from dataclasses import dataclass
from typing import Optional
import os
from pathlib import Path

from .font_calibrator import get_cached_metrics, calculate_font_metrics

UNIFONT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fonts", "unifont.otf")


@dataclass(frozen=True)
class FontConfig:
    """Configuration for a font including metrics and rendering parameters."""
    
    name: str
    path: str
    metrics: dict[int, dict]  # {height: {font_size, offset, pixel_threshold}}
    
    def get_metrics(self, height: int) -> dict:
        """Get metrics for a specific height, computing on the fly if needed."""
        if height in self.metrics:
            return self.metrics[height]
        # Fallback to closest pre-computed height or compute directly
        try:
            return calculate_font_metrics(self.path, height)
        except Exception:
            closest = min(self.metrics.keys(), key=lambda h: abs(h - height))
            return self.metrics[closest]
    
    @classmethod
    def builtin(cls, name: str = "UNIFONT") -> "FontConfig":
        """Load the built-in font by name.
        
        Args:
            name: Name of the built-in font (UNIFONT)
            
        Returns:
            FontConfig for the requested built-in font
            
        Raises:
            ValueError: If font name is not recognized
        """
        if name.upper() != "UNIFONT":
            raise ValueError(f"Unknown built-in font: {name}. Available: UNIFONT")
        return cls.from_file(UNIFONT_PATH, name="UNIFONT")
    
    @classmethod
    def from_file(cls, path: str, name: Optional[str] = None) -> "FontConfig":
        """Load a font from file path, automatically calculating metrics if not cached.
        
        Args:
            path: Path to .ttf or .otf file
            name: Optional display name
                
        Returns:
            FontConfig for the font
            
        Raises:
            FileNotFoundError: If font file does not exist
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"Font file not found: {path}")
        
        font_path = Path(path).resolve()
        font_name = name or font_path.stem
        metrics = get_cached_metrics(str(font_path), heights=(16, 24, 32), font_name=font_name)
        
        return cls(name=font_name, path=str(font_path), metrics=metrics)


def _get_builtin_fonts() -> dict[str, FontConfig]:
    """Lazy dictionary of built-in fonts."""
    if os.path.exists(UNIFONT_PATH):
        try:
            return {"UNIFONT": FontConfig.from_file(UNIFONT_PATH, name="UNIFONT")}
        except Exception:
            pass
    return {}


class _BuiltinFontsProxy(dict):
    """Proxy dict to load built-in fonts on access."""
    def __getitem__(self, item):
        if item.upper() == "UNIFONT":
            return FontConfig.builtin("UNIFONT")
        raise KeyError(f"Unknown built-in font: {item}. Available: UNIFONT")

    def __contains__(self, item):
        return isinstance(item, str) and item.upper() == "UNIFONT"

    def keys(self):
        return ["UNIFONT"]

    def items(self):
        return [("UNIFONT", self["UNIFONT"])]


BUILTIN_FONTS: dict[str, FontConfig] = _BuiltinFontsProxy()


def list_fonts() -> list[str]:
    """List all available built-in fonts.
    
    Returns:
        List of built-in font names
    """
    return ["UNIFONT"]
