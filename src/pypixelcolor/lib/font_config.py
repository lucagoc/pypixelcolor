from dataclasses import dataclass
from typing import Optional
import os
import json
from pathlib import Path


@dataclass(frozen=True)
class FontConfig:
    """Configuration for a font including metrics and rendering parameters."""
    
    name: str
    path: str
    metrics: dict[int, dict]  # {height: {font_size, offset, pixel_threshold}}
    
    def get_metrics(self, height: int) -> dict:
        """Get metrics for a specific height, with fallback to closest height."""
        if height in self.metrics:
            return self.metrics[height]
        # Fallback: find closest height
        closest = min(self.metrics.keys(), key=lambda h: abs(h - height))
        return self.metrics[closest]
    
    @classmethod
    def builtin(cls, name: str) -> "FontConfig":
        """Load a built-in font by name.
        
        Args:
            name: Name of the built-in font (CUSONG, VCR_OSD_MONO, SIMSUN)
            
        Returns:
            FontConfig for the requested built-in font
            
        Raises:
            ValueError: If font name is not recognized
        """
        if name not in BUILTIN_FONTS:
            available = ", ".join(BUILTIN_FONTS.keys())
            raise ValueError(f"Unknown built-in font: {name}. Available: {available}")
        return BUILTIN_FONTS[name]
    
    @classmethod
    def from_file(cls, path: str, name: Optional[str] = None) -> "FontConfig":
        """Load a custom font from file path.
        
        Looks for a JSON configuration file with the same name as the font file.
        For example, if loading "Minecraft.ttf", it will look for "Minecraft.json"
        in the same directory. If the JSON file doesn't exist, uses default metrics.
        
        JSON format:
        {
            "name": "Minecraft",  // Optional display name
            "metrics": {
                "16": {
                    "font_size": 16,
                    "offset": [0, 0],
                    "pixel_threshold": 70,
                    "var_width": false
                },
                "24": { ... },
                ...
            }
        }
        
        Args:
            path: Path to .ttf file
            name: Optional display name (overrides JSON name if provided)
                
        Returns:
            FontConfig for the custom font
            
        Raises:
            FileNotFoundError: If font file does not exist
            ValueError: If JSON configuration is invalid
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"Font file not found: {path}")
        
        # Look for JSON configuration file
        font_path = Path(path)
        json_path = font_path.with_suffix('.json')
        
        # Default metrics if no JSON file exists
        if not json_path.exists():
            font_name = name or font_path.stem
            metrics = {}
            for height in [16, 24, 32]:
                metrics[height] = {
                    "font_size": height,
                    "offset": (0, 0),
                    "pixel_threshold": 70,
                    "var_width": False
                }
            return cls(name=font_name, path=str(font_path), metrics=metrics)
        
        # Load JSON configuration
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {json_path}: {e}")
        
        # Extract name
        font_name = name or config.get("name") or font_path.stem
        
        # Extract and validate metrics
        if "metrics" not in config:
            raise ValueError(f"Missing 'metrics' field in {json_path}")
        
        metrics_data = config["metrics"]
        if not isinstance(metrics_data, dict):
            raise ValueError(f"'metrics' must be a dictionary in {json_path}")
        
        # Convert metrics keys to integers and validate structure
        metrics = {}
        for height_str, metric_dict in metrics_data.items():
            try:
                height = int(height_str)
            except ValueError:
                raise ValueError(f"Invalid height key '{height_str}' in {json_path}, must be an integer")
            
            # Validate required fields
            required_fields = ["font_size", "offset", "pixel_threshold"]
            for field in required_fields:
                if field not in metric_dict:
                    raise ValueError(f"Missing required field '{field}' for height {height} in {json_path}")
            
            # Convert offset from list to tuple if needed
            offset = metric_dict["offset"]
            if isinstance(offset, list):
                if len(offset) != 2:
                    raise ValueError(f"Offset must be a 2-element array for height {height} in {json_path}")
                offset = tuple(offset)
            elif not isinstance(offset, tuple):
                raise ValueError(f"Offset must be an array [x, y] for height {height} in {json_path}")
            
            # Get var_width with default value of False
            var_width = metric_dict.get("var_width", False)
            if not isinstance(var_width, bool):
                raise ValueError(f"'var_width' must be a boolean for height {height} in {json_path}")
            
            metrics[height] = {
                "font_size": int(metric_dict["font_size"]),
                "offset": offset,
                "pixel_threshold": int(metric_dict["pixel_threshold"]),
                "var_width": var_width
            }
        
        if not metrics:
            raise ValueError(f"No valid metrics found in {json_path}")
        
        return cls(name=font_name, path=str(font_path), metrics=metrics)


# Built-in fonts registry - loaded from JSON files
def _load_builtin_fonts() -> dict[str, FontConfig]:
    """Load built-in fonts from the fonts directory."""
    fonts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fonts")
    builtin_fonts = {}
    
    # List of built-in font names
    font_names = ["CUSONG", "VCR_OSD_MONO", "SIMSUN"]
    
    for font_name in font_names:
        font_path = os.path.join(fonts_dir, f"{font_name}.ttf")
        if os.path.exists(font_path):
            try:
                builtin_fonts[font_name] = FontConfig.from_file(font_path)
            except Exception as e:
                # Log error but continue loading other fonts
                import logging
                logging.getLogger(__name__).warning(
                    f"Failed to load built-in font {font_name}: {e}"
                )
    
    return builtin_fonts


BUILTIN_FONTS: dict[str, FontConfig] = _load_builtin_fonts()



def list_fonts() -> list[str]:
    """List all available built-in fonts.
    
    Returns:
        List of built-in font names
    """
    return list(BUILTIN_FONTS.keys())
