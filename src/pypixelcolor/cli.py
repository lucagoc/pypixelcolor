"""
# pypixelcolor cli.py
Command-line interface for iPixel BLE commands
"""

import asyncio
import argparse
import logging
from bleak import BleakScanner

from .lib.logging import setup_logging
from .lib.device_session import DeviceSession
from .websocket import build_command_args
from .commands import COMMANDS

logger = logging.getLogger(__name__)


async def run_commands(commands: list[tuple[str, ...]], address: str) -> None:
    """
    Execute multiple BLE commands sequentially.
    
    Args:
        commands: List of command tuples (command_name, *params).
        address: Bluetooth device address.
    """
    async with DeviceSession(address) as session:
        # Device info is automatically retrieved on connection
        device_info = session.get_device_info()
        logger.info(f"Device: {device_info.width}x{device_info.height} (Type {device_info.led_type})")
        
        for cmd in commands:
            command_name = cmd[0]
            params = cmd[1:]
            
            if command_name == "get_device_info":
                # Special case: get_device_info is now just a getter
                logger.info(str(device_info))
            elif command_name in COMMANDS:
                positional_args, keyword_args = build_command_args(params)
                command_func = COMMANDS[command_name]
                result = await session.execute_command(command_func, *positional_args, **keyword_args)
                
                # Display result if it has data
                if result.data is not None:
                    logger.info(result.format_for_display())
                else:
                    logger.info(f"Command '{command_name}' executed successfully.")
            else:
                logger.error(f"Unknown command: {command_name}")

async def scan_devices() -> None:
    """Scan for Bluetooth devices with 'LED' in their name."""
    logger.info("Scanning for Bluetooth devices...")
    devices = await BleakScanner.discover()
    if devices:
        led_devices = [device for device in devices if device.name and "LED" in device.name]
        logger.info(f"Found {len(led_devices)} device(s):")
        for device in led_devices:
            logger.info(f"  - {device.name} ({device.address})")
    else:
        logger.info("No Bluetooth devices found.")


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="pypixelcolor - CLI")
    parser.add_argument("--scan", action="store_true", help="Scan for Bluetooth devices")
    parser.add_argument(
        "-c", "--command", action="append", nargs="+", metavar="COMMAND PARAMS",
        help="Execute a specific command with parameters. Can be used multiple times."
    )
    parser.add_argument("-a", "--address", help="Specify the Bluetooth device address")
    parser.add_argument("--noemojis", action="store_true", help="Disable emojis in log output")
    parser.add_argument("--loglevel", default="INFO", help="Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")

    args = parser.parse_args()
    
    setup_logging(use_emojis=not args.noemojis, level=args.loglevel)
    if args.scan:
        asyncio.run(scan_devices())
    elif args.command:
        if not args.address:
            logger.error("--address is required when using --command")
            exit(1)
        asyncio.run(run_commands(args.command, args.address))
    else:
        logger.error("No mode specified. Use --scan or -c with -a to specify an address.")
        logger.info("For WebSocket server mode, use: python -m pypixelcolor.websocket -a <address>")


if __name__ == "__main__":
    main()
