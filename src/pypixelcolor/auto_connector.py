"""
Auto-connect module for pypixelcolor.
Automatically discovers and connects to iPixel Color LED panels via Bluetooth.
"""

import asyncio
import logging
from typing import Optional, List
from bleak import BleakScanner

from .lib.device_session import DeviceSession

logger = logging.getLogger(__name__)


class AutoConnector:
    """Automatically discovers and manages connections to iPixel Color LED panels."""
    
    # LED panel device name patterns
    LED_DEVICE_PATTERNS = ["LED_BLE", "iPixel", "PixelColor"]
    
    def __init__(self, auto_reconnect: bool = True, reconnect_interval: int = 5):
        """
        Initialize the AutoConnector.
        
        Args:
            auto_reconnect (bool): Automatically reconnect if connection is lost. Defaults to True.
            reconnect_interval (int): Seconds between reconnection attempts. Defaults to 5.
        """
        self._sessions: dict[str, DeviceSession] = {}  # address -> session
        self._auto_reconnect = auto_reconnect
        self._reconnect_interval = reconnect_interval
        self._discovery_task: Optional[asyncio.Task] = None
        self._reconnect_tasks: dict[str, asyncio.Task] = {}
        self._running = False
    
    async def start_auto_discovery(self) -> None:
        """
        Start automatic discovery and connection of LED panels.
        Runs continuously in the background.
        """
        if self._running:
            logger.warning("Auto-discovery already running")
            return
        
        self._running = True
        logger.info("Starting auto-discovery of LED panels...")
        
        self._discovery_task = asyncio.create_task(self._discovery_loop())
    
    async def stop_auto_discovery(self) -> None:
        """Stop automatic discovery and disconnect all devices."""
        self._running = False
        
        if self._discovery_task:
            self._discovery_task.cancel()
            try:
                await self._discovery_task
            except asyncio.CancelledError:
                pass
        
        # Cancel all reconnect tasks
        for task in self._reconnect_tasks.values():
            task.cancel()
        
        # Disconnect all sessions
        for session in self._sessions.values():
            try:
                await session.disconnect()
            except Exception as e:
                logger.error(f"Error disconnecting: {e}")
        
        self._sessions.clear()
        self._reconnect_tasks.clear()
        logger.info("Auto-discovery stopped")
    
    async def _discovery_loop(self) -> None:
        """Main discovery loop that runs continuously."""
        while self._running:
            try:
                devices = await BleakScanner.discover()
                found_devices = []
                
                # Look for LED devices
                for device in devices:
                    if device.name and any(pattern in device.name for pattern in self.LED_DEVICE_PATTERNS):
                        found_devices.append((device.address, device.name))
                
                # Connect to newly found devices
                for address, name in found_devices:
                    if address not in self._sessions:
                        await self._connect_device(address, name)
                
                # Wait before next scan
                await asyncio.sleep(10)
            
            except Exception as e:
                logger.error(f"Error during discovery: {e}")
                await asyncio.sleep(5)
    
    async def _connect_device(self, address: str, name: str) -> None:
        """
        Connect to a specific device.
        
        Args:
            address: Bluetooth device address
            name: Device name
        """
        try:
            logger.info(f"Attempting to connect to {name} ({address})")
            
            session = DeviceSession(address)
            await session.connect()
            
            self._sessions[address] = session
            device_info = session.get_device_info()
            logger.info(f"✓ Connected to {name}: {device_info.width}x{device_info.height}")
            
            # Start reconnect handler if auto-reconnect is enabled
            if self._auto_reconnect and address not in self._reconnect_tasks:
                task = asyncio.create_task(self._auto_reconnect_handler(address, name))
                self._reconnect_tasks[address] = task
        
        except Exception as e:
            logger.error(f"Failed to connect to {name} ({address}): {e}")
    
    async def _auto_reconnect_handler(self, address: str, name: str) -> None:
        """
        Handle automatic reconnection if connection is lost.
        
        Args:
            address: Bluetooth device address
            name: Device name
        """
        while self._running and address in self._sessions:
            try:
                # Check if connection is still alive
                session = self._sessions[address]
                if session and not session.is_connected():
                    logger.warning(f"Lost connection to {name} ({address}), attempting to reconnect...")
                    await session.disconnect()
                    del self._sessions[address]
                    
                    # Attempt reconnection
                    await asyncio.sleep(self._reconnect_interval)
                    await self._connect_device(address, name)
                
                await asyncio.sleep(5)
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in reconnect handler for {address}: {e}")
                await asyncio.sleep(self._reconnect_interval)
    
    def get_connected_devices(self) -> List[tuple[str, str]]:
        """
        Get list of connected devices.
        
        Returns:
            List of (address, device_name) tuples
        """
        connected = []
        for address, session in self._sessions.items():
            try:
                if session and session.is_connected():
                    device_info = session.get_device_info()
                    name = f"{device_info.width}x{device_info.height}"
                    connected.append((address, name))
            except Exception:
                pass
        return connected
    
    def get_session(self, address: str) -> Optional[DeviceSession]:
        """
        Get a connected session by address.
        
        Args:
            address: Bluetooth device address
            
        Returns:
            DeviceSession if connected, None otherwise
        """
        return self._sessions.get(address)
    
    async def send_command_to_all(self, command_func, *args, **kwargs):
        """
        Send a command to all connected devices.
        
        Args:
            command_func: The command function to execute
            *args: Positional arguments for the command
            **kwargs: Keyword arguments for the command
        """
        tasks = []
        for address, session in self._sessions.items():
            try:
                if session and session.is_connected():
                    task = asyncio.create_task(
                        session.execute_command(command_func, *args, **kwargs)
                    )
                    tasks.append((address, task))
            except Exception as e:
                logger.error(f"Error sending command to {address}: {e}")
        
        # Wait for all commands to complete
        for address, task in tasks:
            try:
                await task
                logger.debug(f"Command sent to {address}")
            except Exception as e:
                logger.error(f"Command failed for {address}: {e}")