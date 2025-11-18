#!/usr/bin/env python3
"""
Generate client.pyi stub file from COMMANDS dictionary.

This script automatically generates type stubs for the Client and AsyncClient classes
based on the command functions defined in the COMMANDS dictionary. This ensures that
IDE autocompletion and type checking stay in sync with available commands.

Usage:
    python scripts/generate_client_stubs.py
"""

import sys
import inspect
from pathlib import Path
from typing import get_type_hints

# Add src to path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root / "src"))

from pypixelcolor.commands import COMMANDS


def format_type_annotation(annotation) -> str:
    """Format a type annotation to a string.
    
    Args:
        annotation: The type annotation
        
    Returns:
        Formatted type string
    """
    if annotation == inspect.Parameter.empty:
        return ""
    
    # Handle type objects
    if isinstance(annotation, type):
        return annotation.__name__
    
    # Convert to string and clean it up
    type_str = str(annotation)
    
    # Remove <class '...'> wrapper
    if type_str.startswith("<class '") and type_str.endswith("'>"):
        type_str = type_str[8:-2]
    
    # Handle typing module types
    type_str = type_str.replace("typing.", "")
    
    return type_str


def get_function_signature(func) -> tuple[str, str]:
    """Extract function signature and return type annotation.
    
    Args:
        func: The function to inspect
        
    Returns:
        Tuple of (parameters_string, return_type)
    """
    sig = inspect.signature(func)
    params = []
    
    for param_name, param in sig.parameters.items():
        # Build parameter string with type hints and defaults
        param_str = param_name
        
        # Add type annotation if available
        if param.annotation != inspect.Parameter.empty:
            type_str = format_type_annotation(param.annotation)
            if type_str:
                param_str += f": {type_str}"
        
        # Add default value if available
        if param.default != inspect.Parameter.empty:
            if isinstance(param.default, str):
                param_str += f' = "{param.default}"'
            elif param.default is None:
                param_str += " = None"
            elif isinstance(param.default, bool):
                param_str += f" = {param.default}"
            else:
                param_str += f" = {param.default}"
        
        params.append(param_str)
    
    params_str = ", ".join(params)
    
    # Try to infer return type from the function
    return_type = infer_return_type(func)
    
    return params_str, return_type


def infer_return_type(func) -> str:
    """Infer the return type of a command function.
    
    Checks if the function returns a SendPlan with a response_handler,
    and if so, extracts the return type from that handler.
    
    Args:
        func: The command function
        
    Returns:
        String representation of the return type
    """
    try:
        # Call the function with dummy arguments to get the SendPlan
        sig = inspect.signature(func)
        
        # Build dummy arguments based on signature
        dummy_args = []
        dummy_kwargs = {}
        for param_name, param in sig.parameters.items():
            if param.default != inspect.Parameter.empty:
                continue  # Skip parameters with defaults
            
            # Provide dummy values based on annotation
            if param.annotation == str or param.annotation == inspect.Parameter.empty:
                dummy_args.append("")
            elif param.annotation == int:
                dummy_args.append(0)
            elif param.annotation == bool:
                dummy_args.append(False)
            else:
                dummy_args.append(None)
        
        # Call the function to get the SendPlan
        plan = func(*dummy_args, **dummy_kwargs)
        
        # Check if it has a response_handler
        if hasattr(plan, 'response_handler') and plan.response_handler is not None:
            # Get the return type from the response_handler
            handler_sig = inspect.signature(plan.response_handler)
            if handler_sig.return_annotation != inspect.Parameter.empty:
                return_annotation = handler_sig.return_annotation
                
                # Extract the actual type from Awaitable or Coroutine
                import typing
                if hasattr(typing, 'get_args'):
                    args = typing.get_args(return_annotation)
                    if args:
                        # Get the inner type (e.g., DeviceInfo from Awaitable[DeviceInfo])
                        inner_type = args[0]
                        if hasattr(inner_type, '__name__'):
                            return inner_type.__name__
                        return str(inner_type).replace('pypixelcolor.lib.device_info.', '')
                
                # Fallback: try to get name directly
                if hasattr(return_annotation, '__name__'):
                    return return_annotation.__name__
                
                return str(return_annotation).replace('pypixelcolor.lib.device_info.', '')
    
    except Exception as e:
        # If we can't infer, default to None
        pass
    
    return "None"


def format_docstring(doc: str | None, indent: int = 8) -> str:
    """Format a docstring with proper indentation.
    
    Args:
        doc: The docstring to format
        indent: Number of spaces to indent
        
    Returns:
        Formatted docstring or empty string
    """
    if not doc:
        return ""
    
    # Get first line of docstring (brief description)
    first_line = doc.strip().split('\n')[0]
    indent_str = " " * indent
    return f'\n{indent_str}"""' + first_line + '"""'


def generate_method_stub(method_name: str, func, is_async: bool = True) -> str:
    """Generate a method stub for the .pyi file.
    
    Args:
        method_name: Name of the method
        func: The command function
        is_async: Whether this is an async method
        
    Returns:
        The method stub as a string
    """
    params_str, return_type = get_function_signature(func)
    doc = format_docstring(func.__doc__)
    
    async_keyword = "async " if is_async else ""
    
    # Add 'self' parameter
    if params_str:
        params_str = f"self, {params_str}"
    else:
        params_str = "self"
    
    stub = f"    {async_keyword}def {method_name}({params_str}) -> {return_type}:{doc}\n        ...\n"
    return stub


def generate_pyi_file() -> str:
    """Generate the complete client.pyi file content.
    
    Returns:
        The complete .pyi file content as a string
    """
    header = '''"""Type stubs for client module to enable IDE autocomplete.

This file is auto-generated by scripts/generate_client_stubs.py
DO NOT EDIT MANUALLY - your changes will be overwritten.
"""

from typing import Union, Optional
from pathlib import Path
from .lib.device_info import DeviceInfo

class AsyncClient:
    """Asynchronous client for controlling the LED matrix via BLE."""
    
    def __init__(self, address: str) -> None: ...
    
    async def connect(self) -> None:
        """Connect to the BLE device and retrieve device info."""
        ...
    
    async def disconnect(self) -> None:
        """Disconnect from the BLE device."""
        ...
    
    def get_device_info(self) -> DeviceInfo:
        """Get cached device information.
        
        Device info is automatically retrieved during connect().
        This is a simple getter for the cached data.
        """
        ...
    
'''
    
    # Generate method stubs for all commands
    method_stubs = []
    for cmd_name, cmd_func in sorted(COMMANDS.items()):
        stub = generate_method_stub(cmd_name, cmd_func, is_async=True)
        method_stubs.append(stub)
    
    # Add context manager methods
    context_methods = '''    async def __aenter__(self) -> AsyncClient: ...
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None: ...


'''
    
    # Now generate Client class (synchronous wrapper)
    client_header = '''class Client:
    """Synchronous client for controlling the LED matrix via BLE."""
    
    def __init__(self, address: str) -> None: ...
    
    def connect(self) -> None:
        """Connect to the BLE device and retrieve device info."""
        ...
    
    def disconnect(self) -> None:
        """Disconnect from the BLE device."""
        ...
    
    def get_device_info(self) -> DeviceInfo:
        """Get cached device information.
        
        Device info is automatically retrieved during connect().
        This is a simple getter for the cached data.
        """
        ...
    
'''
    
    # Generate synchronous versions of all command methods
    sync_method_stubs = []
    for cmd_name, cmd_func in sorted(COMMANDS.items()):
        stub = generate_method_stub(cmd_name, cmd_func, is_async=False)
        sync_method_stubs.append(stub)
    
    # Add context manager methods for Client
    sync_context_methods = '''    def __enter__(self) -> Client: ...
    def __exit__(self, exc_type, exc_val, exc_tb) -> None: ...
'''
    
    # Combine everything
    pyi_content = (
        header +
        "".join(method_stubs) +
        context_methods +
        client_header +
        "".join(sync_method_stubs) +
        sync_context_methods
    )
    
    return pyi_content


def main():
    """Main entry point."""
    print("🔧 Generating client.pyi from COMMANDS dictionary...")
    
    # Generate the content
    pyi_content = generate_pyi_file()
    
    # Write to file
    output_path = repo_root / "src" / "pypixelcolor" / "client.pyi"
    output_path.write_text(pyi_content, encoding="utf-8")
    
    print(f"✅ Generated {output_path}")
    print(f"📊 Added {len(COMMANDS)} command methods")
    print(f"📄 Total lines: {len(pyi_content.splitlines())}")
    
    # Show which commands were added
    print("\n📋 Commands included:")
    for cmd_name in sorted(COMMANDS.keys()):
        print(f"   - {cmd_name}")
    
    print("\n🎉 Done! The client.pyi file has been updated.")


if __name__ == "__main__":
    main()
