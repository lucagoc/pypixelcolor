"""
Device session management for BLE connections.

This module provides a centralized way to manage BLE connections and device information.
DeviceInfo is automatically retrieved on connection and cached for the session lifetime.
"""

import inspect
import logging
from typing import Optional
from bleak import BleakClient

from .constants import NOTIFY_UUID
from .device_info import DeviceInfo
from .transport.send_plan import send_plan
from .transport.ack_manager import AckManager
from .command_result import CommandResult

logger = logging.getLogger(__name__)


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
    
    def __init__(self, address: str):
        """
        Initialize a device session.
        
        Args:
            address: Bluetooth device address (e.g., "1D:6B:5E:B5:A5:54")
        """
        self._address = address
        self._client: Optional[BleakClient] = None
        self._ack_mgr: Optional[AckManager] = None
        self._device_info: Optional[DeviceInfo] = None
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
    
    async def connect(self) -> DeviceInfo:
        """
        Connect to the BLE device and retrieve device information.
        
        This method:
        1. Establishes BLE connection
        2. Enables notifications
        3. Automatically retrieves device info
        4. Caches device info for the session
        
        Returns:
            DeviceInfo object with device specifications.
            
        Raises:
            RuntimeError: If already connected.
            Exception: If connection or device info retrieval fails.
        """
        if self._connected:
            raise RuntimeError("Already connected")
        
        logger.info(f"Connecting to {self._address}...")
        self._client = BleakClient(self._address)
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
        
        if self._device_info:
            logger.info(f"Device info cached: {self._device_info.width}x{self._device_info.height} "
                       f"(Type {self._device_info.led_type})")
            return self._device_info
        else:
            raise RuntimeError("Failed to retrieve device info")
    
    async def disconnect(self) -> None:
        """
        Disconnect from the BLE device.
        
        Cleans up notifications and closes the BLE connection.
        """
        if not self._connected:
            logger.warning("Not connected")
            return
        
        try:
            if self._client:
                await self._client.stop_notify(NOTIFY_UUID)
        except Exception as e:
            logger.debug(f"Error stopping notifications: {e}")
        
        if self._client:
            await self._client.disconnect()
        
        self._connected = False
        self._client = None
        self._ack_mgr = None
        self._device_info = None
        logger.info("Disconnected")
    
    async def _fetch_device_info(self) -> None:
        """
        Internal method to fetch device info from the device.
        
        This is called automatically during connect().
        """
        from .internal_commands import build_get_device_info_command, _handle_device_info_response
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
        return await send_plan(self._client, plan, self._ack_mgr)
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
