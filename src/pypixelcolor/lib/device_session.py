"""
Device session management for BLE connections.

This module provides a centralized way to manage BLE connections and device information.
DeviceInfo is automatically retrieved on connection and cached for the session lifetime.
"""

import inspect
import logging
from typing import Optional

from bleak import BleakClient, BleakScanner

from .constants import NOTIFY_UUID
from .device_info import DeviceInfo
from .transport.send_plan import send_plan
from .transport.ack_manager import AckManager
from .command_result import CommandResult

logger = logging.getLogger(__name__)


# Scan window used before a connect attempt. The panel only accepts a
# connection while it advertises, so a bounded scan is needed; the
# window is a maximum — the scan returns as soon as the panel is seen.
DEFAULT_CONNECT_SCAN_TIMEOUT = 15.0


class PanelNotAdvertisingError(RuntimeError):
    """Raised when the panel is not advertising before connect.

    A panel that is not advertising cannot accept a BLE connection:
    usually a phone already holds the connection through the iPixel
    app (the panel stops advertising while connected), or the panel
    is powered off / out of range.
    """


class DeviceSession:
    """
    Manages a BLE session with automatic device info retrieval.
    
    This class handles:
    - BLE connection lifecycle
    - Automatic device info retrieval on connection
    - Command execution with device_info injection
    - Cached access to device information
    
    Example:
        async with DeviceSession("1D:6B:5E:B5:A5:54") as session:
            info = session.get_device_info()
            print(f"Screen: {info.width}x{info.height}")
            
            result = await session.execute_command("set_brightness", 50)
    """
    
    def __init__(
        self,
        address: str,
        *,
        write_with_response: bool = True,
        connect_scan_timeout: float = DEFAULT_CONNECT_SCAN_TIMEOUT,
    ):
        """
        Initialize a device session.

        Args:
            address: Bluetooth device address (e.g., "1D:6B:5E:B5:A5:54")
            write_with_response: Write BLE chunks with response (default) or without, see send_plan().
            connect_scan_timeout: Seconds to scan for the panel's
                advertisement before connecting. The panel only
                accepts a connection while advertising (a phone
                connected to the panel stops it advertising), so
                scanning first turns a blind GATT connect into a
                fast, actionable error. Set to 0 to skip the scan and
                connect directly by address.
        """
        self._address = address
        self._write_with_response = write_with_response
        self._connect_scan_timeout = connect_scan_timeout
        self._client: Optional[BleakClient] = None
        self._ack_mgr: Optional[AckManager] = None
        self._device_info: Optional[DeviceInfo] = None
        self._connected = False
    
    def _on_disconnect(self, client):
        """Callback when the BLE device disconnects."""
        logger.info(f"BLE device disconnected: {self._address}")
        self._connected = False
    
    @property
    def address(self) -> str:
        """Get the device address."""
        return self._address
    
    @property
    def device_info(self) -> Optional[DeviceInfo]:
        """Get cached device information (None if not connected)."""
        return self._device_info
    
    @property
    def is_connected(self) -> bool:
        """Check if the session is connected."""
        return self._connected
    
    def get_device_info(self) -> DeviceInfo:
        """
        Get device information.
        
        Returns:
            Cached DeviceInfo object.
            
        Raises:
            RuntimeError: If not connected or device info not available.
        """
        if not self._connected:
            raise RuntimeError("Not connected. Call connect() first.")
        if self._device_info is None:
            raise RuntimeError("Device info not available.")
        return self._device_info
    
    async def _pre_scan(self) -> None:
        """Verify the panel is advertising before attempting a connect.

        A panel only accepts a BLE connection while it advertises; a
        phone already connected to the panel (the panel stops
        advertising while connected) or an off panel cannot be
        reached. Scanning first turns a blind GATT connect into a
        fast, actionable error.

        Raises:
            PanelNotAdvertisingError: If the address was not seen
                within ``connect_scan_timeout``.
        """
        if self._connect_scan_timeout <= 0:
            return
        logger.info(
            f"Scanning for {self._address} for "
            f"{self._connect_scan_timeout:.0f}s ..."
        )
        device = await BleakScanner.find_device_by_address(
            self._address, timeout=self._connect_scan_timeout
        )
        if device is None:
            raise PanelNotAdvertisingError(
                f"Panel {self._address} not seen advertising for "
                f"{self._connect_scan_timeout:.0f}s. A panel only accepts "
                "a connection while it advertises. Check: (1) a phone is "
                "not connected to the panel through the iPixel app — "
                "close the app or switch the phone's Bluetooth off; "
                "(2) the panel is powered (5 V / 2 A); (3) the panel "
                "is in range."
            )
        name = getattr(device, "name", None) or ""
        rssi = getattr(device, "rssi", None)
        logger.info(
            f"Found {self._address}"
            + (f" '{name}'" if name else "")
            + (f" (RSSI {rssi} dBm)" if rssi is not None else "")
        )

    async def connect(self) -> DeviceInfo:
        """
        Connect to the BLE device and retrieve device information.
        
        This method:
        1. Scans for the panel's advertisement
        2. Establishes BLE connection
        3. Enables notifications
        4. Automatically retrieves device info
        5. Caches device info for the session
        
        Returns:
            DeviceInfo object with device specifications.
            
        Raises:
            RuntimeError: If already connected.
            PanelNotAdvertisingError: If the panel is not advertising.
            Exception: If connection or device info retrieval fails.
        """
        if self._connected:
            raise RuntimeError("Already connected")

        if self._client is not None:
            await self._close_connection()

        await self._pre_scan()

        logger.info(f"Connecting to {self._address}...")
        self._client = BleakClient(self._address, disconnected_callback=self._on_disconnect)
        try:
            await self._client.connect()
            self._connected = True
            logger.info(f"Connected to {self._address}")

            # Enable notify-based ACKs
            self._ack_mgr = AckManager()
            try:
                await self._client.start_notify(NOTIFY_UUID, self._ack_mgr.make_notify_handler())
            except Exception as e:
                logger.warning(f"Failed to enable notifications on {NOTIFY_UUID}: {e}")

            # Retrieve device info automatically
            logger.debug("Retrieving device information...")
            await self._fetch_device_info()
        except Exception:
            await self._close_connection()
            raise

        if self._device_info:
            logger.info(f"Device info cached: {self._device_info.width}x{self._device_info.height} "
                       f"(Type {self._device_info.led_type})")
            return self._device_info

        await self._close_connection()
        raise RuntimeError("Failed to retrieve device info")
    
    async def _close_connection(self) -> None:
        """Close the BLE client and reset cached state (even if partial)."""
        client, self._client = self._client, None
        self._ack_mgr = None
        self._device_info = None
        self._connected = False
        if client is None:
            return
        try:
            if client.is_connected:
                try:
                    await client.stop_notify(NOTIFY_UUID)
                except Exception as e:
                    logger.debug(f"Error stopping notifications: {e}")
            await client.disconnect()
        except Exception as e:
            logger.debug(f"Error closing BLE connection: {e}")
    
    async def disconnect(self) -> None:
        """
        Disconnect from the BLE device.
        
        Cleans up notifications and closes the BLE connection.
        """
        if not self._connected and self._client is None:
            logger.warning("Not connected")
            return
        
        await self._close_connection()
        logger.info("Disconnected")
    
    async def _fetch_device_info(self) -> None:
        """
        Internal method to fetch device info from the device.
        
        This is called automatically during connect().
        """
        from .internal_commands import (
            build_get_device_info_command,
            build_get_hw_info_command,
            _handle_device_info_response,
            _handle_hw_info_response,
        )
        from .transport.send_plan import single_window_plan
        
        if not self._client or not self._ack_mgr:
            raise RuntimeError("Client or AckManager not initialized")
        
        # Build and send the device info request
        payload = build_get_device_info_command()
        plan = single_window_plan(
            "get_device_info_internal",
            payload,
            requires_ack=False,
            response_handler=_handle_device_info_response
        )
        
        result = await send_plan(self._client, plan, self._ack_mgr)
        
        if result.data is None:
            raise RuntimeError("Failed to retrieve device info")

        # Firmware versions come from a separate 0x8005 read; best effort.
        hw_plan = single_window_plan(
            "get_hw_info_internal",
            build_get_hw_info_command(),
            requires_ack=False,
            response_handler=_handle_hw_info_response
        )
        try:
            hw_result = await send_plan(self._client, hw_plan, self._ack_mgr)
            if hw_result.data:
                result.data.mcu_version, result.data.wifi_version = hw_result.data
        except Exception as e:
            logger.warning(f"Failed to read firmware versions: {e}")
        
        self._device_info = result.data
    
    async def execute_command(self, command_func, *args, **kwargs) -> CommandResult:
        """
        Execute a command with automatic device_info injection.
        
        If the command function accepts a 'device_info' parameter,
        it will be automatically injected with the cached device info.
        
        Args:
            command_func: The command function to execute
            *args: Positional arguments for the command
            **kwargs: Keyword arguments for the command
            
        Returns:
            CommandResult from the command execution.
            
        Raises:
            RuntimeError: If not connected.
        """
        if not self._connected:
            raise RuntimeError("Not connected. Call connect() first.")
        
        if not self._client or not self._ack_mgr:
            raise RuntimeError("Client or AckManager not initialized")
        
        # Inject device_info if the command accepts it
        sig = inspect.signature(command_func)
        if 'device_info' in sig.parameters and self._device_info is not None:
            kwargs['device_info'] = self._device_info
        
        # Build the SendPlan
        plan = command_func(*args, **kwargs)
        
        # Execute the plan
        return await send_plan(self._client, plan, self._ack_mgr,
                               write_with_response=self._write_with_response)
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
