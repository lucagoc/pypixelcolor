"""
# pypixelcolor cli.py
Command-line interface for iPixel BLE commands
"""

import asyncio
import argparse
import logging
import sys
from contextlib import contextmanager
from rich.console import Console

from .scanner import scan_devices as discover_devices
from .lib.logging import setup_logging
from .lib.device_session import DeviceSession
from .websocket import build_command_args
from .commands import COMMANDS
from .__version__ import VERSION

logger = logging.getLogger(__name__)


class InteractiveStatusHandler(logging.Handler):
    """Logging handler that routes logs to a Rich Console and status spinner."""

    def __init__(self, console: Console, status):
        super().__init__()
        self.console = console
        self.status = status

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = record.getMessage()
            if record.levelno >= logging.ERROR:
                self.console.print(f"[bold red][ERROR][/bold red] {msg}")
            elif record.levelno >= logging.WARNING:
                self.console.print(f"[bold yellow][WARN][/bold yellow] {msg}")
            elif record.name != "pypixelcolor.cli" or msg.endswith("..."):
                self.status.update(f"[cyan]{msg}[/cyan]")
            elif msg.startswith("  -"):
                self.console.print(msg)
            elif msg.startswith("Connected") or msg.startswith("Command") or msg.startswith("Found"):
                self.console.print(f"[bold green][OK][/bold green] {msg}")
            else:
                self.console.print(f"[bold blue][INFO][/bold blue] {msg}")
        except Exception:
            self.handleError(record)


@contextmanager
def interactive_status(initial_status: str = "Working..."):
    """Context manager setting up Rich status spinner and redirecting logs."""
    console = Console(highlight=False)
    with console.status(f"[cyan]{initial_status}[/cyan]", spinner="dots") as status:
        handler = InteractiveStatusHandler(console, status)
        root_logger = logging.getLogger()
        
        old_handlers = root_logger.handlers[:]
        old_level = root_logger.level
        
        root_logger.handlers = [handler]
        root_logger.setLevel(logging.INFO)
        try:
            yield console
        finally:
            root_logger.handlers = old_handlers
            root_logger.setLevel(old_level)


async def run_commands(commands: list[tuple[str, ...]], address: str) -> None:
    """
    Execute multiple BLE commands sequentially.
    
    Args:
        commands: List of command tuples (command_name, *params).
        address: Bluetooth device address.
    """
    logger.info(f"Connecting to {address}...")
    async with DeviceSession(address) as session:
        device_info = session.get_device_info()
        
        for cmd in commands:
            command_name = cmd[0]
            params = cmd[1:]
            
            logger.info(f"Executing '{command_name}'...")
            
            if command_name == "get_device_info":
                logger.info(str(device_info))
            elif command_name in COMMANDS:
                positional_args, keyword_args = build_command_args(params)
                command_func = COMMANDS[command_name]
                result = await session.execute_command(command_func, *positional_args, **keyword_args)
                
                if result.data is not None:
                    logger.info(result.format_for_display())
                elif result.success:
                    logger.info(f"Command '{command_name}' executed successfully.")
                else:
                    logger.error(f"Command '{command_name}' failed: {result.message}")
            else:
                logger.error(f"Unknown command: {command_name}")

            logger.info("Exiting...")

async def scan_devices() -> None:
    """Scan for Bluetooth devices with 'LED' in their name."""
    logger.info("Scanning for Bluetooth devices...")
    devices = await discover_devices()

    if not devices:
        logger.error("No LED devices found.")
        return

    logger.info(f"Found {len(devices)} LED device(s):")
    for device in devices:
        logger.info(f"  - {device.name} ({device.address})")


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description=f"pypixelcolor - CLI v{VERSION}")
    parser.add_argument("--scan", action="store_true", help="Scan for Bluetooth devices")
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}", help="Show the version and exit")
    parser.add_argument(
        "-c", "--command", action="append", nargs="+", metavar="COMMAND PARAMS",
        help="Execute a specific command with parameters. Can be used multiple times."
    )
    parser.add_argument("-a", "--address", help="Specify the Bluetooth device address")
    parser.add_argument(
        "--loglevel",
        default=None,
        help="Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL). Specifying any loglevel disables the interactive spinner.",
    )

    args = parser.parse_args()
    
    loglevel_specified = args.loglevel is not None
    is_interactive = not loglevel_specified and sys.stdout.isatty()

    def run_app() -> None:
        try:
            if args.scan:
                asyncio.run(scan_devices())
            elif args.command:
                if not args.address:
                    logger.error("--address is required when using --command")
                    sys.exit(1)
                asyncio.run(run_commands(args.command, args.address))
            else:
                logger.error("No mode specified. Use --scan or -c with -a to specify an address.")
                logger.info("For WebSocket server mode, use: python -m pypixelcolor.websocket -a <address>")
        except KeyboardInterrupt:
            logger.info("Interrupted by user.")
            sys.exit(0)
        except Exception as e:
            if loglevel_specified and args.loglevel.upper() == "DEBUG":
                logger.error(f"An error occurred: {e}")
                logger.exception("Traceback (DEBUG):")
            else:
                logger.error(f"An error occurred: {e}. Run with --loglevel DEBUG to see the full traceback.")
            sys.exit(1)

    if is_interactive:
        with interactive_status("Starting..."):
            run_app()
    else:
        setup_logging(level=args.loglevel.upper() if args.loglevel else "INFO")
        run_app()

if __name__ == "__main__":
    main()
