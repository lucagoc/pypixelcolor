"""
Device information data structures and parsing.
"""

from dataclasses import dataclass
from typing import Optional


# Device type to LED type mapping (from Go implementation)
DEVICE_TYPE_MAP = {
    128: 0,   # -128 -> Type 0 (64x64)
    129: 2,   # -127 -> Type 2 (32x32)
    130: 4,   # -126 -> Type 4 (32x16)
    131: 3,   # -125 -> Type 3 (64x16)
    132: 1,   # -124 -> Type 1 (96x16)
    133: 5,   # -123 -> Type 5 (64x20)
    134: 6,   # -122 -> Type 6 (128x32)
    135: 7,   # -121 -> Type 7 (144x16)
    136: 8,   # -120 -> Type 8 (192x16)
    137: 9,   # -119 -> Type 9 (48x24)
    138: 10,  # -118 -> Type 10 (64x32)
    139: 11,  # -117 -> Type 11 (96x32)
    140: 12,  # -116 -> Type 12 (128x32)
    141: 13,  # -115 -> Type 13 (96x32)
    142: 14,  # -114 -> Type 14 (160x32)
    143: 15,  # -113 -> Type 15 (192x32)
    144: 16,  # -112 -> Type 16 (256x32)
    145: 17,  # -111 -> Type 17 (320x32)
    146: 18,  # -110 -> Type 18 (384x32)
    147: 19,  # -109 -> Type 19 (448x32)
}

# LED size map (width, height)
LED_SIZE_MAP = {
    0: (64, 64),
    1: (96, 16),
    2: (32, 32),
    3: (64, 16),
    4: (32, 16),
    5: (64, 20),
    6: (128, 32),
    7: (144, 16),
    8: (192, 16),
    9: (48, 24),
    10: (64, 32),
    11: (96, 32),
    12: (128, 32),
    13: (96, 32),
    14: (160, 32),
    15: (192, 32),
    16: (256, 32),
    17: (320, 32),
    18: (384, 32),
    19: (448, 32),
}


@dataclass
class DeviceInfo:
    """Information retrieved from the LED device."""
    
    device_type: int
    """Device type byte from response"""
    
    mcu_version: str
    """MCU firmware version (Major.Minor)"""
    
    wifi_version: str
    """WiFi/BLE firmware version (Major.Minor)"""
    
    width: int
    """LED matrix width"""
    
    height: int
    """LED matrix height"""
    
    has_wifi: bool
    """Whether device supports WiFi"""
    
    password_flag: int
    """Password requirement flag (255 = no password)"""
    
    led_type: Optional[int] = None
    """LED type derived from device type"""
    
    def __str__(self):
        """Format device info for display."""
        lines = [
            "Device Information:",
            f"  Device Type: {self.device_type} (LED Type: {self.led_type})",
            f"  Screen Size: {self.width}x{self.height}",
            f"  MCU Version: {self.mcu_version}",
            f"  WiFi/BLE Version: {self.wifi_version}",
            f"  WiFi Support: {'Yes' if self.has_wifi else 'No'}",
            f"  Password Flag: {self.password_flag}",
        ]
        return "\n".join(lines)


def parse_device_info(response: bytes) -> DeviceInfo:
    """Parse device info response from the LED device.
    
    Args:
        response: Raw bytes received from the device.
        
    Returns:
        Parsed DeviceInfo object.
        
    Raises:
        ValueError: If response is too short or invalid.
    """
    if len(response) < 5:
        raise ValueError(f"Response too short: got {len(response)} bytes, need at least 5")
    
    # Extract device type from byte 4
    device_type_byte = response[4]
    # device_type_byte = 129 # Force a device for debug
    
    # Map device type to LED type
    led_type = DEVICE_TYPE_MAP.get(device_type_byte, 0)
    
    # Get screen dimensions from LED size map
    dimensions = LED_SIZE_MAP.get(led_type, (64, 64))
    width, height = dimensions
    
    # Parse version information (not implemented in this snippet)
    mcu_version = "unknown"
    wifi_version = "unknown"
    
    # WiFi capability based on device type (same)
    has_wifi = False
    
    # Extract password flag
    password_flag = response[10] if len(response) >= 11 else 255
    
    return DeviceInfo(
        device_type=device_type_byte,
        mcu_version=mcu_version,
        wifi_version=wifi_version,
        width=width,
        height=height,
        has_wifi=has_wifi,
        password_flag=password_flag,
        led_type=led_type,
    )
