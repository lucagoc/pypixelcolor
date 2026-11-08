"""
Internal commands used by the system (not exposed to users).

These commands are used internally for system operations like
retrieving device information during connection setup.
"""

import logging
from datetime import datetime

from .device_info import parse_device_info, parse_hw_info, DeviceInfo

logger = logging.getLogger(__name__)


def build_get_device_info_command() -> bytes:
    """
    Build the get device info command payload.
    
    Command format: [8, 0, 1, 128, hour, minute, second, language]
    
    Returns:
        Command bytes to send to the device.
    """
    now = datetime.now()
    cmd = bytes([
        8,                 # Command header
        0,                 # Reserved
        1,                 # Sub-command
        0x80,              # -128 in signed byte
        now.hour,          # Current hour
        now.minute,        # Current minute
        now.second,        # Current second
        0,                 # Language (0 for default)
    ])
    return cmd


def build_get_hw_info_command() -> bytes:
    """
    Build the get firmware versions command payload.

    Command format: [4, 0, 5, 128]. The reply is
    `08 00 05 80 <mcu major> <mcu minor> <wifi major> <wifi minor>`.
    This is a separate command from the `0x8001` device-info read; versions are
    not part of the `0x8001` reply.

    Returns:
        Command bytes to send to the device.
    """
    return bytes([4, 0, 5, 0x80])


async def _handle_device_info_response(client, response: bytes) -> DeviceInfo:
    """
    Parse the device info response.
    
    Args:
        client: BleakClient (unused but required by response_handler signature).
        response: Raw response bytes from the device.
        
    Returns:
        Parsed DeviceInfo object.
    """
    logger.debug(f"Parsing device info response: {response.hex()}")
    return parse_device_info(response)


async def _handle_hw_info_response(client, response: bytes) -> tuple:
    """
    Parse the firmware versions response.

    Args:
        client: BleakClient (unused but required by response_handler signature).
        response: Raw response bytes from the device.

    Returns:
        ``(mcu_version, wifi_version)`` tuple.
    """
    logger.debug(f"Parsing hw info response: {response.hex()}")
    return parse_hw_info(response)
