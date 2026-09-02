"""
Auto-connect CLI for pypixelcolor.
Automatically discovers and connects to LED panels with persistent connection.
"""

import asyncio
import argparse
import logging

from .lib.logging import setup_logging
from .auto_connector import AutoConnector
from .commands import COMMANDS
from .__version__ import VERSION

logger = logging.getLogger(__name__)


async def main_auto_connect(command_args: list = None, command_name: str = None) -> None:
    """
    Main auto-connect mode that continuously manages LED panel connections.
    
    Args:
        command_args: Optional command to run on connected devices
        command_name: Name of the command to run
    """
    connector = AutoConnector(auto_reconnect=True, reconnect_interval=5)
    
    try:
        await connector.start_auto_discovery()
        
        # If a command is specified, wait for devices and send command
        if command_name and command_name in COMMANDS:
            logger.info(f"Waiting for devices to connect before executing: {command_name}")
            await asyncio.sleep(3)  # Wait for discovery
            
            devices = connector.get_connected_devices()
            if devices:
                logger.info(f"Sending command '{command_name}' to {len(devices)} device(s)")
                command_func = COMMANDS[command_name]
                await connector.send_command_to_all(command_func, *command_args)
            else:
                logger.warning("No devices found")
        else:
            # Keep running indefinitely
            logger.info("Auto-connector running. Press Ctrl+C to stop.")
            logger.info("Connected devices will appear below:")
            
            while True:
                await asyncio.sleep(30)
                devices = connector.get_connected_devices()
                if devices:
                    logger.info(f"Currently connected: {', '.join([f'{name} ({addr})' for addr, name in devices])}")
    
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        await connector.stop_auto_discovery()


def main():
    """Main CLI entry point for auto-connect mode."""
    parser = argparse.ArgumentParser(
        description=f"pypixelcolor Auto-Connect - v{VERSION}\nAutomatically discover and manage LED panel connections"
    )
    
    parser.add_argument(
        "--auto", action="store_true", help="Enable auto-connect mode"
    )
    parser.add_argument(
        "--command", "-c", help="Command to send (e.g., 'set_clock_mode')"
    )
    parser.add_argument(
        "--params", "-p", nargs="*", help="Parameters for the command"
    )
    parser.add_argument(
        "--noemojis", action="store_true", help="Disable emojis in log output"
    )
    parser.add_argument(
        "--loglevel", default="INFO", help="Set logging level"
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {VERSION}"
    )
    
    args = parser.parse_args()
    setup_logging(use_emojis=not args.noemojis, level=args.loglevel)
    
    if args.auto:
        asyncio.run(main_auto_connect(
            command_args=args.params or [],
            command_name=args.command
        ))
    else:
        logger.error("Use --auto flag to enable auto-connect mode")
        parser.print_help()


if __name__ == "__main__":
    main()