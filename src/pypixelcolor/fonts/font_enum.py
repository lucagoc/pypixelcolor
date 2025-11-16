from enum import Enum
from typing import Any


class Font(Enum):
    """
    Enum Font for available fonts in the library.
    """
    
    CUSONG = "0_CUSONG16"
    VCR_OSD_MONO = "1_VCR_OSD_MONO"
    SIMSUN = "2_SIMSUN"

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value

    @classmethod
    def from_str(cls, val: Any) -> "Font":
        """Convert a string or Font to enum Font.

        Accepts either the enum member, the enum name (e.g. "FONSUG") or the
        raw value (e.g. "0_FONSUG"). Raises ValueError if unknown.
        """
        if isinstance(val, cls):
            return val
        if not isinstance(val, str):
            raise ValueError(f"Invalid font type: {type(val)!r}")
        # match by value or by name
        for member in cls:
            if member.value == val or member.name == val:
                return member
        raise ValueError(f"Unknown font: {val}")

# Mapping
FONT_METRICS: dict[Font, dict[int, dict[str, Any]]] = {
    Font.CUSONG: {
        16: {
            "font_size": 16,
            "offset": (0, -1),
            "is_16bit": False
        },
        20: {
            "font_size": 20,
            "offset": (0, 0),
            "is_16bit": True
        },
        24: {
            "font_size": 24,
            "offset": (0, 0),
            "is_16bit": True
        },
        32: {
            "font_size": 32,
            "offset": (0, 0),
            "is_16bit": True
        }
    },
    Font.VCR_OSD_MONO: {
        16: {
            "font_size": 16,
            "offset": (0, 0),
            "is_16bit": True
        },
        20: {
            "font_size": 20,
            "offset": (0, 0),
            "is_16bit": True
        },
        24: {
            "font_size": 24,
            "offset": (0, 0),
            "is_16bit": True
        },
        32: {
            "font_size": 32,
            "offset": (0, 0),
            "is_16bit": True
        }
    },
    Font.SIMSUN: {
        16: {
            "font_size": 16,
            "offset": (0, 0),
            "is_16bit": False
        },
        20: {
            "font_size": 20,
            "offset": (0, 0),
            "is_16bit": True
        },
        24: {
            "font_size": 24,
            "offset": (0, 0),
            "is_16bit": True
        },
        32: {
            "font_size": 32,
            "offset": (0, 0),
            "is_16bit": True
        }
    }
}