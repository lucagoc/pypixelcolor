"""
Generic command result structure for commands that return data.
"""

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class CommandResult:
    """Result of a command execution.
    
    This allows commands to return structured data that can be:
    - Displayed by the CLI
    - Returned directly when used as a library
    - Serialized for WebSocket responses
    """
    
    success: bool = True
    """Whether the command executed successfully"""
    
    data: Optional[Any] = None
    """Optional data returned by the command (e.g., DeviceInfo)"""
    
    message: Optional[str] = None
    """Optional message about the execution"""
    
    def __bool__(self):
        """Allow using result in boolean context."""
        return self.success
    
    def format_for_display(self) -> str:
        """Format the result for CLI display.
        
        Subclasses or data objects should implement __str__ for custom formatting.
        The CLI will call this method to display results.
        """
        if self.data is not None:
            # If data has a custom string representation, use it
            if hasattr(self.data, '__str__') and type(self.data).__str__ is not object.__str__:
                return str(self.data)
            # Otherwise, try to format it nicely
            return repr(self.data)
        elif self.message:
            return self.message
        elif self.success:
            return "Command executed successfully"
        else:
            return "Command failed"
