"""
Bluetooth LE device discovery for iPixel LED matrices.
"""

import asyncio
from bleak import BleakScanner
from bleak.backends.device import BLEDevice


async def scan_devices(timeout: float = 5.0) -> list[BLEDevice]:
    """
    Scan for compatible LED devices asynchronously.

    Args:
        timeout: Scanning duration in seconds (default: 5.0).

    Returns:
        A list of discovered BLEDevice objects matching LED devices.
    """
    devices = await BleakScanner.discover(timeout=timeout)
    return [d for d in devices if d.name and "LED" in d.name]


def scan_devices_sync(timeout: float = 5.0) -> list[BLEDevice]:
    """
    Scan for compatible LED devices synchronously.

    Args:
        timeout: Scanning duration in seconds (default: 5.0).

    Returns:
        A list of discovered BLEDevice objects matching LED devices.
    """
    return asyncio.run(scan_devices(timeout=timeout))
