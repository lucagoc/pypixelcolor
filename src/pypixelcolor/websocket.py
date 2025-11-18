"""
# pypixelcolor websocket.py
WebSocket server for BLE communication
"""

import json
import logging
import argparse
import asyncio
import websockets

from .lib.logging import setup_logging
from .lib.device_session import DeviceSession
from .commands import COMMANDS

logger = logging.getLogger(__name__)

# Global device session shared across all WebSocket connections
_device_session = None

def build_command_args(params):
    """Parse command parameters into positional and keyword arguments."""
    positional_args = []
    keyword_args = {}
    for param in params:
        if "=" in param:
            key, value = param.split("=", 1)
            keyword_args[key.replace('-', '_')] = value
        else:
            positional_args.append(param)
    return positional_args, keyword_args


async def handle_websocket(websocket):
    """Handle WebSocket connections and execute BLE commands."""
    global _device_session
    
    if _device_session is None or not _device_session.is_connected:
        logger.error("Device session is not available")
        return
    
    device_info = _device_session.get_device_info()
    logger.info(f"WebSocket client connected. Device: {device_info.width}x{device_info.height} (Type {device_info.led_type})")
    
    try:
        while True:
            # Wait for a message from the client
            message = await websocket.recv()

            # Parse JSON
            try:
                command_data = json.loads(message)
                command_name = command_data.get("command")
                params = command_data.get("params", [])

                if command_name == "get_device_info":
                    # Special case: get_device_info is now just a getter
                    response = {
                        "status": "success",
                        "command": command_name,
                        "data": {
                            "device_type": device_info.device_type,
                            "mcu_version": device_info.mcu_version,
                            "wifi_version": device_info.wifi_version,
                            "width": device_info.width,
                            "height": device_info.height,
                            "has_wifi": device_info.has_wifi,
                            "password_flag": device_info.password_flag,
                            "led_type": device_info.led_type,
                        }
                    }
                elif command_name in COMMANDS:
                    # Separate positional and keyword arguments
                    positional_args, keyword_args = build_command_args(params)

                    # Build the SendPlan and execute it
                    command_func = COMMANDS[command_name]
                    result = await _device_session.execute_command(command_func, *positional_args, **keyword_args)

                    # Prepare the response
                    response = {"status": "success", "command": command_name}
                    
                    # If the command returned data, include it in the response
                    if result.data is not None:
                        # Try to serialize the data
                        try:
                            from dataclasses import asdict, is_dataclass
                            # If data is a dataclass, convert to dict
                            if is_dataclass(result.data) and not isinstance(result.data, type):
                                response["data"] = asdict(result.data)
                            # If data has a __dict__, use it
                            elif hasattr(result.data, '__dict__'):
                                response["data"] = result.data.__dict__
                            else:
                                response["data"] = str(result.data)
                        except Exception as e:
                            logger.warning(f"Failed to serialize command data: {e}")
                            response["data"] = str(result.data)
                else:
                    response = {"status": "error", "message": "Commande inconnue"}
            except Exception as e:
                response = {"status": "error", "message": str(e)}

            # Send the response to the client
            await websocket.send(json.dumps(response))
    except websockets.ConnectionClosed:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"Error in WebSocket handler: {e}")


async def start_server(ip, port, address):
    """Start the WebSocket server and maintain BLE connection."""
    global _device_session
    
    # Initialize and connect to the device once
    logger.info(f"Connecting to BLE device {address}...")
    _device_session = DeviceSession(address)
    try:
        await _device_session.connect()
        logger.info(f"BLE device connected and ready")
        
        # Start the WebSocket server
        server = await websockets.serve(handle_websocket, ip, port)
        logger.info(f"WebSocket server started on ws://{ip}:{port}")
        
        # Keep the server running
        await server.wait_closed()
    finally:
        # Disconnect when the server stops
        if _device_session and _device_session.is_connected:
            logger.info("Disconnecting from BLE device...")
            await _device_session.disconnect()


if __name__ == "__main__":    
    parser = argparse.ArgumentParser(description="WebSocket BLE Server")
    parser.add_argument("-p", "--port", type=int, default=4444, help="Specify the port for the server")
    parser.add_argument("--host", default="localhost", help="Bind address (e.g., 0.0.0.0, ::, or localhost)")
    parser.add_argument("-a", "--address", required=True, help="Specify the Bluetooth device address")
    parser.add_argument("--noemojis", action="store_true", help="Disable emojis in log output")
    
    args = parser.parse_args()
    
    setup_logging(use_emojis=not args.noemojis)

    asyncio.run(start_server(args.host, args.port, args.address))
