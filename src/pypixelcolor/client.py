"""
File for pypixel package.
Provides synchronous and asynchronous clients for controlling LED matrix.
"""

import asyncio
import logging
from typing import Optional

from .lib.device_session import DeviceSession
from .lib.device_info import DeviceInfo
from .commands import COMMANDS

logger = logging.getLogger(__name__)

def _create_async_method(command_name: str, command_func):
    """Create an async method for a command.
    
    Args:
        command_name: Name of the command
        command_func: The command function from COMMANDS
    
    Returns:
        An async method that can be added to AsyncClient
    """
    async def method(self, *args, **kwargs):
        await self._ensure_connected()
        
        # Execute command through session (handles device_info injection)
        result = await self._session.execute_command(command_func, *args, **kwargs)
        
        # Log success
        if result.data is None:
            logger.info(f"Command '{command_name}' executed successfully")
        else:
            logger.debug(f"Command '{command_name}' executed successfully with data")
        
        # Return the data directly (not the CommandResult wrapper)
        # This makes the API cleaner: client.get_device_info() returns DeviceInfo, not CommandResult
        return result.data
    
    # Preserve the original function's metadata for better introspection
    method.__name__ = command_name
    method.__doc__ = command_func.__doc__
    
    return method


class AsyncClient:
    """Asynchronous client for controlling the LED matrix via BLE."""
    
    def __init__(self, address: str):
        """Initialize the AsyncClient.
        
        Args:
            address: Bluetooth device address (e.g., "1D:6B:5E:B5:A5:54")
        """
        self._session = DeviceSession(address)
        self._connected = False
    
    async def connect(self) -> None:
        """Connect to the BLE device and retrieve device info."""
        if self._connected:
            logger.warning("Already connected")
            return
        
        await self._session.connect()
        self._connected = True
    
    async def disconnect(self) -> None:
        """Disconnect from the BLE device."""
        if not self._connected:
            logger.warning("Not connected")
            return
        
        await self._session.disconnect()
        self._connected = False
    
    def get_device_info(self) -> DeviceInfo:
        """
        Get cached device information.
        
        Device info is automatically retrieved during connect().
        This is a simple getter for the cached data.
        
        Returns:
            DeviceInfo object with device specifications.
            
        Raises:
            RuntimeError: If not connected.
        """
        return self._session.get_device_info()
    
    async def _ensure_connected(self) -> None:
        """Ensure the client is connected."""
        if not self._connected:
            raise RuntimeError("Client not connected. Call connect() first")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()


# Dynamically add command methods to AsyncClient
for cmd_name, cmd_func in COMMANDS.items():
    setattr(AsyncClient, cmd_name, _create_async_method(cmd_name, cmd_func))

class Client:
    """Synchronous client for controlling the LED matrix via BLE.
    
    This is a synchronous wrapper around AsyncClient that handles the event loop
    automatically for simpler usage in non-async code.
    """
    
    def __init__(self, address: str):
        """Initialize the Client.
        
        Args:
            address: Bluetooth device address (e.g., "1D:6B:5E:B5:A5:54")
        """
        self._async_client = AsyncClient(address)
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._loop_thread = None
        self._setup_loop()
    
    def _setup_loop(self):
        """Set up a persistent event loop in a separate thread."""
        import threading
        
        def start_loop(loop):
            asyncio.set_event_loop(loop)
            loop.run_forever()
        
        self._loop = asyncio.new_event_loop()
        self._loop_thread = threading.Thread(target=start_loop, args=(self._loop,), daemon=True)
        self._loop_thread.start()
    
    def _run_async(self, coro):
        """Run an async coroutine synchronously using the persistent loop."""
        if self._loop is None:
            raise RuntimeError("Event loop not initialized")
        
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result()
    
    def __getattr__(self, name: str):
        """Delegate attribute access to async client, wrapping coroutines.
        
        This allows automatic synchronous wrapping of all async methods without
        explicit redefinition, reducing code duplication.
        """
        attr = getattr(self._async_client, name)
        
        # If it's a coroutine function, wrap it to run synchronously
        if asyncio.iscoroutinefunction(attr):
            def sync_wrapper(*args, **kwargs):
                return self._run_async(attr(*args, **kwargs))
            # Preserve function metadata for better IDE support
            sync_wrapper.__name__ = name
            sync_wrapper.__doc__ = attr.__doc__
            return sync_wrapper
        
        # Otherwise return the attribute as-is
        return attr
    
    def _cleanup_loop(self):
        """Clean up the event loop."""
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
    
    def __del__(self):
        """Cleanup on deletion."""
        try:
            if self._async_client._connected:
                self.disconnect()
        except Exception:
            pass
        finally:
            self._cleanup_loop()
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
